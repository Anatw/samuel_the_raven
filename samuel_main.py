import asyncio
import signal
import maestro
import multiprocessing
import threading
import queue
import sys
from os import environ

from samuel_async import Samuel
from Servo import Movement
from animatron_move import Move
from camera_face_tracking import FaceDetection, face_event_listener
from touch_sensor import MPR121TouchSensor

# from speech_recognition import SpeechRecognition
from timer_window_for_programmer import show_timer_window

samuel = None
maestro_controller = None
audio_queue = None
face_queue = None
shutdown_in_progress = False


def run_timer_window_on_pi(threads):
    # Check if running directly on the Raspberry Pi (not via SSH)
    if "SSH_CONNECTION" in environ:
        environ.pop("DISPLAY", None)
        environ["QT_QPA_PLATFORM"] = "offscreen"
        environ["LIBGL_ALWAYS_INDIRECT"] = "1"
    else:
        timer_thread = threading.Thread(target=show_timer_window, daemon=True)
        threads.append(timer_thread)


def signal_handler(signum, frame):
    # This function is meant to handle exit by the user (ctrl+x).
    samuel.events.shutdown_event.set()
    if shutdown_in_progress:
        # If they really hammer Ctrl-C again, let the default handler kill us
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        return


def terminate_all():
    # Ensure all threads are stopped and resources are cleaned up.
    global threads, processes, maestro_controller, face_queue
    print("Treminating, please don't touch the keyboard ot shut down the program.")

    if samuel:  # only signal shutdown if Samuel was actually created
        samuel.events.shutdown_event.set()

    if threads:
        for thread in threads:
            if not thread.daemon and thread.is_alive():
                thread.join(timeout=1)

    if face_queue:
        face_queue.close()
        face_queue.join_thread()

    if maestro_controller:
        maestro_controller.close()

    print("All threads, processes, and resources have been cleaned up.")


def main():
    global threads, samuel, audio_queue, maestro_controller, face_queue

    # Initiate the servo object. You can find the correct tty by running 'ls /dev/tty*' and
    # checking for new ttys before and after connecting the Pololu Maestro using USB.
    maestro_controller = maestro.Controller(ttyStr="/dev/ttyACM0")
    touch_sensor = MPR121TouchSensor(
        i2c_bus=1,
        address=0x5A,
        electrode=11,
        touch_thresh=12,
        release_thresh=6,
        dt=1,
        dr=3,
        touch_conf=4,
        release_conf=5,
        poll_interval=0.1,
    )
    audio_queue = queue.PriorityQueue()
    samuel = Samuel(touch_sensor=touch_sensor, audio_queue=audio_queue)

    # Set mouth movements to be faster:
    maestro_controller.setSpeed(chan=Movement.mouth.pin_number, speed=150)  # 100
    maestro_controller.setAccel(chan=Movement.mouth.pin_number, accel=180)  # 180
    # Faster wing movement:
    maestro_controller.setSpeed(chan=Movement.wings.pin_number, speed=30)
    maestro_controller.setAccel(chan=Movement.wings.pin_number, accel=120)
    # Set body speed and acceleration movement:
    maestro_controller.setSpeed(chan=Movement.body.pin_number, speed=4)
    maestro_controller.setAccel(chan=Movement.body.pin_number, accel=10)
    # Set head speed and acceleration movement:
    maestro_controller.setSpeed(chan=Movement.head_ud.pin_number, speed=120)
    maestro_controller.setAccel(chan=Movement.head_ud.pin_number, accel=8)
    maestro_controller.setSpeed(chan=Movement.head_rl.pin_number, speed=120)
    maestro_controller.setAccel(chan=Movement.head_rl.pin_number, accel=8)
    # speech_instance = SpeechRecognition(sample_rate=48000)
    face_queue = multiprocessing.Queue()
    face_detection_instance = FaceDetection(samuel=samuel, face_queue=face_queue)
    try:
        threads = []
        run_timer_window_on_pi(threads)

        # Use threads for I/O-bound tasks
        threads += [
            threading.Thread(target=samuel.blinker.blink, daemon=True),
            threading.Thread(target=samuel.head_pat, daemon=True),
            threading.Thread(target=samuel.look_at_me, daemon=True),
            # threading.Thread(
            #     target=sounddevice_worker,
            #     args=(audio_queue, audio_folder_path, samuel.events.shutdown_event),
            #     daemon=True
            # ),
            threading.Thread(
                target=lambda: asyncio.run(
                    samuel.speaker.speak_worker_loop(
                        audio_queue, samuel.events.shutdown_event
                    )
                ),
                daemon=True,
            ),
            threading.Thread(
                target=face_event_listener,
                args=(face_queue, audio_queue, samuel),
                daemon=False,  # joined later, after closing the queue cleanly
            ),
            threading.Thread(
                target=face_detection_instance.face_detection_and_tracking, daemon=True
            ),
            threading.Thread(target=Move(samuel.events).move, daemon=True),
        ]

        for thread in threads:
            thread.start()

        samuel.events.shutdown_event.wait()
        terminate_all()
        sys.exit(0)

    except Exception as e:
        print(f"An error occurred: {e}")
        terminate_all()


if __name__ == "__main__":
    # Assign handler function for the user termination option (cntl+x):
    signal.signal(signal.SIGINT, signal_handler)
    multiprocessing.set_start_method("spawn", force=True)
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        terminate_all()
        sys.exit(1)
