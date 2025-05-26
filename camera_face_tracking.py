import collections
from pathlib import Path
import cv2  # OpenCV library for image processing
from picamera2 import Picamera2
import face_recognition
import numpy as np
import pickle
import threading
import time

from Servo import Movement
from animatron_speak import Speak
from private_face_behaviors import FaceRecognization
from private_face_behaviors import Names

# Constants explanation:
# FRAME_WIDTH: The rightes point in the image. Constant value reteieved with frams.shape
# FRAME_HEIGHT: The lowest (buttom) point in the image. Constant value reteieved with frams.shape.
#               The image top point value is 0.
# CV_SCALER: (4) this has to be a whole number.
# TIME_TO_TRACK_FACE: The time in seconds to track the face before going back to random movements.
# BOREDOM_TIME: The time in seconds to stay in idle movement mode even when a face is detected.
# FACE_METCH_TOLERANCE: The tolerance for the face recognition. Lower value = stricter.
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
CV_SCALER = 4
TIME_TO_TRACK_FACE = 100
BOREDOM_TIME = 60
IMAGE_THIRD = FRAME_HEIGHT / 3
UNRECOGNIZED_FACE = "unknown"
FACE_METCH_TOLERANCE = 0.45
# To get the ration between the frame (0-1920) and the servo range we need to get the ratio
# between the range and devide with the frame top value:
head_rl_ratio = (Movement.head_rl.max_value - Movement.head_rl.min_value) / FRAME_WIDTH
head_ud_ratio = (Movement.head_ud.max_value - Movement.head_ud.min_value) / FRAME_HEIGHT
head_ud_ratio_third = head_ud_ratio / 3
body_ratio = (Movement.body.max_value - Movement.body.min_value) / FRAME_HEIGHT


class FaceDetecion:
    def __init__(
        self,
        samuel,
        face_queue,
        encoding_path=Path(
            "~/samuel_the_raven/Face Recognition/encodings.pickle"
        ).expanduser(),
    ):
        self.samuel = samuel
        self.face_queue = face_queue
        self.known_face_encodings, self.known_face_names = (
            self._load_trained_face_encodings(encoding_path=encoding_path)
        )

        self.blinker = samuel.blinker
        self.speaker = Speak(blinker=self.blinker)
        self._face_recognization = FaceRecognization(samuel)
        self.face_tracking_duration = TIME_TO_TRACK_FACE
        self.camera = self._init_camera()
        self.match_counts = collections.Counter()

        self.currently_tracked_face = UNRECOGNIZED_FACE  # live - who’s on screen now
        self.tracked_face = UNRECOGNIZED_FACE  # snapshot at tracking session start
        self.bored_from_face = UNRECOGNIZED_FACE  # A face Samuel bored of
        self.bored_until = 0
        self.face_locations = []
        self.prev_face_locations = []
        self.face_encodings = []
        self.face_names = []

    @staticmethod
    def _load_trained_face_encodings(encoding_path):
        print("[INFO] loading encodings...")
        with open(encoding_path, "rb") as f:
            data = pickle.loads(f.read())
        return data["encodings"], data["names"]

    @staticmethod
    def _init_camera():
        picam2 = Picamera2()
        picam2.configure(
            picam2.create_preview_configuration(
                main={"format": "XRGB8888", "size": (FRAME_WIDTH, FRAME_HEIGHT)}
            )
        )
        picam2.start()
        return picam2

    @staticmethod
    def process_frame(frame):
        # Resize frame - increase performance (less pixels processed, less time spent)
        resized_frame = cv2.resize(
            frame,
            (0, 0),
            fx=(1 / CV_SCALER),
            fy=(1 / CV_SCALER),
            interpolation=cv2.INTER_AREA,
        )
        flipped_frame = cv2.flip(resized_frame, 1)

        # Convert the image from BGR to RGB colour space (facial recognition lib uses RGB, OpenCV uses BGR)
        rgb_resized_frame = cv2.cvtColor(flipped_frame, cv2.COLOR_BGR2RGB)

        return rgb_resized_frame

    def _begin_tracking(self, name: str):
        self.tracked_face = name
        print(f"Pickaboo! I see you {self.tracked_face}!")
        self.samuel.events.face_detected_event.set()
        self.samuel.events.resume_face_tracking_event.clear()
        self.face_queue.put(name)
        threading.Timer(self.face_tracking_duration, self._tracking_timeout).start()

    def search_for_faces(self, frame, return_boxes: bool = False):
        # Find all the faces and face encodings in the current frame of video
        self.face_locations = face_recognition.face_locations(
            frame, number_of_times_to_upsample=0, model="hog"
        )
        if not self.face_locations and self.prev_face_locations:
            # reuse previous box if detector blinked
            self.face_locations = self.prev_face_locations.copy()
        elif self.face_locations:
            self.prev_face_locations = self.face_locations.copy()
        self.face_encodings = face_recognition.face_encodings(
            frame, self.face_locations, model="cnn"
        )

        self.face_names = []
        for face_encoding in self.face_encodings:
            name = UNRECOGNIZED_FACE
            matches = face_recognition.compare_faces(
                self.known_face_encodings, face_encoding, tolerance=FACE_METCH_TOLERANCE
            )
            # Use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(
                self.known_face_encodings, face_encoding
            )
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
            self.face_names.append(name)

        recognised = [n for n in self.face_names if n in Names.names]
        if not recognised:
            return

        name = recognised[0]
        self.currently_tracked_face = name
        if name == self.bored_from_face and time.time() < self.bored_until:
            return  # keep ignoring, move to idle movements
        # If we reach here either boredom expired, or this is a new face → I'm interested again
        self.bored_from_face = UNRECOGNIZED_FACE
        self.bored_until = 0

        if self.samuel.events.resume_face_tracking_event.is_set():
            self._begin_tracking(name)

        if return_boxes:
            # convert (top, right, bottom, left) in small frame back to (x, y, w, h) in the full frame
            boxes = []
            for top, right, bottom, left in self.face_locations:
                x = int(left * CV_SCALER)
                y = int(top * CV_SCALER)
                w = int((right - left) * CV_SCALER)
                h = int((bottom - top) * CV_SCALER)
                boxes.append((x, y, w, h))

            return self.face_names, boxes

    def _tracking_timeout(self):
        """
        Called after TIME_TO_TRACK_FACE seconds.
        If the same person is still in view, mark them as boring.
        """
        print("Tracking window ended — deciding whether to get bored…")

        if (
            self.tracked_face == self.currently_tracked_face
            and self.tracked_face != UNRECOGNIZED_FACE
        ):
            self.bored_from_face = self.tracked_face
            self.bored_until = time.time() + BOREDOM_TIME
            print(
                f"I'm bored of {self.bored_from_face}; "
                f"idle for {BOREDOM_TIME}s (until {self.bored_until:.0f})."
            )
        else:
            self.bored_from_face = UNRECOGNIZED_FACE
            self.bored_until = 0
            print("Face changed/gone — just resuming idle movements.")

        # Turn back to idle motion
        self.samuel.events.face_detected_event.clear()

    def samuel_track_face(self):
        if self.samuel.events.face_detected_event.is_set():
            # TODO: Add a Kraa random sound here!
            for top, right, bottom, left in self.face_locations:
                # Scale back up face locations since the frame we detected in was scaled
                bottom *= CV_SCALER
                right *= CV_SCALER
                top *= CV_SCALER
                left *= CV_SCALER
                face_lr_middle = (right + left) / 2
                face_ud_middle = (top + bottom) / 2
                # Change the head_ud_ratio when needed -> The highr the face is in the frame window, the smalest the ratio should be.
                image_third_face_location = int(face_ud_middle // IMAGE_THIRD) + 1
                head_ud_ratio = head_ud_ratio_third * (image_third_face_location)
                if image_third_face_location == 1:
                    Movement.body.set_position(
                        Movement.body.get_position() - 50
                    )  # move body up
                if image_third_face_location == 3:
                    Movement.body.set_position(
                        Movement.body.get_position() + 100
                    )  # move body down
                eye_offset_ratio = 0.1  # 20% of face width to one side
                eye_offset_pixels = (right - left) * eye_offset_ratio
                if face_lr_middle > FRAME_WIDTH // 2:
                    face_lr_middle -= eye_offset_pixels
                else:
                    face_lr_middle += eye_offset_pixels

                Movement.head_rl.set_position(
                    target_value=int(
                        Movement.head_rl.min_value + (face_lr_middle * head_rl_ratio)
                    )
                )

                Movement.head_ud.set_position(
                    target_value=int(
                        Movement.head_ud.max_value - (face_ud_middle * head_ud_ratio)
                    )
                )
        else:
            return

    def face_detection_and_tracking(self):
        self.samuel.events.resume_face_tracking_event.set()
        try:
            while not self.samuel.events.shutdown_event.is_set():
                frame = self.camera.capture_array()
                processed = self.process_frame(frame=frame)
                self.search_for_faces(frame=processed)
                self.samuel_track_face()

        finally:
            self.camera.stop()
