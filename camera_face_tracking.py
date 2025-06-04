import heapq
from pathlib import Path
import queue
from random import choices, uniform
import cv2  # OpenCV library for image processing
from picamera2 import Picamera2
from config import BlinkConfig
from constants import FACE_TRACKING_TIMEOUT
import face_recognition
import numpy as np
import pickle
import threading
import time

from Servo import Movement
from animatron_speak import Speak
from private_face_behaviors import Names

# Frame dimensions:
# FRAME_WIDTH: The rightmost point in the image. Constant value retrieved with frame.shape
# FRAME_HEIGHT: The lowest (bottom) point in the image. Constant value retrieved with frame.shape. The image top point value is 0.
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080

# CV_SCALER: How much to scale down the frame for face detection. This has to be a whole number.
CV_SCALER = 4

# Face recognition settings:
# BOREDOM_TIME: The time in seconds to stay in idle movement mode even when a face is detected.
# FACE_MATCH_TOLERANCE: The tolerance for the face recognition. Lower value = stricter.
BOREDOM_TIME = 60
IMAGE_THIRD = FRAME_HEIGHT / 3
UNRECOGNIZED_FACE = "unknown"
FACE_MATCH_TOLERANCE = 0.38
# To get the ratio between the frame (0-1920) and the servo range we need to get the ratio
# between the range and divide with the frame top value:
head_rl_ratio = (Movement.head_rl.max_value - Movement.head_rl.min_value) / FRAME_WIDTH
head_ud_ratio = (Movement.head_ud.max_value - Movement.head_ud.min_value) / FRAME_HEIGHT
head_ud_ratio_third = head_ud_ratio / 3


def face_event_listener(face_queue, audio_queue, samuel):
    """
    Pull names from face_queue, pick number of repeats, and enqueue filenames
    into audio_queue for playback.
    """

    def _flush_below(priority_queue: queue.PriorityQueue, min_priority: int) -> None:
        """
        Remove any queued items whose priority >= min_priority and rebuild the heap in-place.
        """
        with priority_queue.mutex:
            priority_queue.queue[:] = [
                item for item in priority_queue.queue if item[0] < min_priority
            ]
            heapq.heapify(priority_queue.queue)  # restore heap property

    while not samuel.events.shutdown_event.is_set():
        try:
            name = face_queue.get(timeout=0.2)  # blocks
        except (EOFError, OSError):  # main has closed the queue — time to exit
            break
        except queue.Empty:  # timeout: loop back and check shutdown_event
            continue

        samuel.events.face_detected_event.set()

        number_of_repeats = [1, 2, 3]
        weights_for_repeats = [
            0.55,
            0.30,
            0.15,
        ]  # 1 chances are 55%, 2 are 30%, 3 are 15%
        reps = choices(number_of_repeats, weights=weights_for_repeats, k=1)[0]
        print(f"Repeating name {reps} time(s)")

        # blink faster while speaking
        samuel.blinker.change_blinking_time(
            BlinkConfig.ATTENTION_FAST, BlinkConfig.ATTENTION_SLOW
        )

        track = Speak.choose_random_sound_from_category(category=name)
        _flush_below(audio_queue, 1)
        for _ in range(reps):
            audio_queue.put_nowait((0, track, uniform(0.3, 2.2)))

        samuel.blinker.restore_blinking_time()


class FaceDetection:
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
        self.face_tracking_duration = FACE_TRACKING_TIMEOUT
        self.camera = self._init_camera()

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

    def _tracking_timeout(self):
        """
        Update boredom state when the tracking faces window ends.
        """
        if (
            self.tracked_face == self.currently_tracked_face
            and self.tracked_face != UNRECOGNIZED_FACE
        ):
            self.bored_from_face = self.tracked_face
            self.bored_until = time.time() + BOREDOM_TIME
            print(f"I'm bored of {self.bored_from_face}; idle for {BOREDOM_TIME}s.")
        else:
            self.bored_from_face = UNRECOGNIZED_FACE
            self.bored_until = 0
            print("Face changed/gone — just resuming idle movements.")

        # Turn back to idle motion:
        self.samuel.events.face_detected_event.clear()

    def _begin_tracking(self, name: str):
        self.tracked_face = name
        print(f"Pickaboo! I see you {self.tracked_face}!")
        self.samuel.events.face_detected_event.set()
        self.samuel.events.face_tracking_activate_event.clear()
        self.face_queue.put(name)
        threading.Timer(self.face_tracking_duration, self._tracking_timeout).start()

    def samuel_track_face(self):
        if self.samuel.events.face_detected_event.is_set():
            # TODO: Add a Kraa random sound here every random time!
            scale = CV_SCALER  # Reduce multiple calls to global constant
            for top, right, bottom, left in self.face_locations:
                # scale HOG box back to the original frame size
                bottom *= scale
                right *= scale
                top *= scale
                left *= scale
                face_lr_middle = (right + left) / 2
                face_ud_middle = (top + bottom) / 2
                # Determine which vertical “third” the face is in (1=top, 2=middle, 3=bottom);
                # then scale head_ud_ratio so Samuel’s neck moves less when the face is higher.
                image_third_face_location = int(face_ud_middle // IMAGE_THIRD) + 1
                scaled_head_ud_ratio = head_ud_ratio_third * (image_third_face_location)
                if image_third_face_location == 1:
                    Movement.body.set_position(
                        Movement.body.get_position() - 50
                    )  # move body up
                if image_third_face_location == 3:
                    Movement.body.set_position(
                        Movement.body.get_position() + 100
                    )  # move body down

                # 10% 'eye offset' keeps gaze bird-natural
                eye_offset = (right - left) * 0.1
                if face_lr_middle > FRAME_WIDTH // 2:
                    face_lr_middle -= eye_offset
                else:
                    face_lr_middle += eye_offset

                Movement.head_rl.set_position(
                    target_value=int(
                        Movement.head_rl.min_value + (face_lr_middle * head_rl_ratio)
                    )
                )
                Movement.head_ud.set_position(
                    target_value=int(
                        Movement.head_ud.max_value
                        - (face_ud_middle * scaled_head_ud_ratio)
                    )
                )
        else:
            return

    def search_for_faces(self, frame, return_boxes: bool = False):
        """
        Find all the faces and face encodings in the current frame of video.
        """
        # Using model="hog" here because it’s faster on a Pi,
        # but the trade‐off is slightly lower accuracy than CNN.
        self.face_locations = face_recognition.face_locations(
            frame, number_of_times_to_upsample=0, model="hog"
        )
        if not self.face_locations and self.prev_face_locations:
            # If HOG missed (face_locations is empty), reuse previous boxes:
            self.face_locations = self.prev_face_locations.copy()
        elif self.face_locations:
            self.prev_face_locations = self.face_locations.copy()
        # Using model="cnn" for higher‐quality 128-dim embeddings.
        # This is CPU‐heavy—on a Pi. Change to "hog" to go easier on the CPU.
        self.face_encodings = face_recognition.face_encodings(
            frame, self.face_locations, model="cnn"
        )

        self.face_names = []
        for face_encoding in self.face_encodings:
            name = UNRECOGNIZED_FACE
            matches = face_recognition.compare_faces(
                self.known_face_encodings, face_encoding, tolerance=FACE_MATCH_TOLERANCE
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

        if self.samuel.events.face_tracking_activate_event.is_set():
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
        return None

    def face_detection_and_tracking(self):
        self.samuel.events.face_tracking_activate_event.set()
        try:
            while not self.samuel.events.shutdown_event.is_set():
                frame = self.camera.capture_array()
                processed = self.process_frame(frame=frame)
                self.search_for_faces(frame=processed)
                self.samuel_track_face()

        finally:
            self.camera.stop()
