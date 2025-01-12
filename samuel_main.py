import RPi.GPIO as GPIO
import signal
import maestro
import multiprocessing
import threading
import sys
from os import environ

from samuel_async import Samuel
from Servo import Movement
from animatron_move import Move
from camera_face_tracking import FaceDetecion
from timer_window_for_programmer import show_timer_window


# Initiate the servo object. You can find the correct tty by running 'ls /dev/tty*' and
# checking for new ttys before and after connecting the Pololu Maestro using USB.
maestro_controller = maestro.Controller(ttyStr="/dev/ttyACM0")


def signal_handler():
    # This function is meant to handle exit by the user (ctrl+x).
    print("Caught termination signal. Cleaning up...")
    terminate_all()
    GPIO.cleanup()
    sys.exit(0)


def terminate_all():
    # Ensure all threads and processes are stopped and resources are cleaned up.
    global threads, processes, maestro_controller

    # Terminate threads
    for thread in threads:
        if thread.is_alive():
            thread.join(timeout=1)

    # Terminate processes
    for process in processes:
        if process.is_alive():
            process.terminate()
            process.join()

    # Close the maestro controller
    maestro_controller.close()

    print("All threads, processes, and resources have been cleaned up.")


def main():
    global threads, processes
    samuel = Samuel()
    # Assign handler function for the user termination option (cntl+x):
    signal.signal(signal.SIGINT, signal_handler)
    # Set mouth movements to be faster:
    maestro_controller.setSpeed(chan=Movement.mouth.pin_number, speed=100)
    maestro_controller.setAccel(chan=Movement.mouth.pin_number, accel=180)
    # Faster wing movement:
    maestro_controller.setSpeed(chan=Movement.wings.pin_number, speed=20)
    maestro_controller.setAccel(chan=Movement.wings.pin_number, accel=120)
    # Set body speed and acceleration movement:
    maestro_controller.setSpeed(chan=Movement.body.pin_number, speed=4)
    maestro_controller.setAccel(chan=Movement.body.pin_number, accel=10)
    # Set head speed and acceleration movement:
    maestro_controller.setSpeed(chan=Movement.head_ud.pin_number, speed=80)
    maestro_controller.setAccel(chan=Movement.head_ud.pin_number, accel=5)
    maestro_controller.setSpeed(chan=Movement.head_rl.pin_number, speed=80)
    maestro_controller.setAccel(chan=Movement.head_rl.pin_number, accel=5)
    move_instance = Move()
    face_detection_instance = FaceDetecion(samuel=samuel)
    try:
        threads = []
        processes = []

        # Check if running directly on the Raspberry Pi (not via SSH)
        if "SSH_CONNECTION" not in environ:
            timer_thread = threading.Thread(target=show_timer_window, daemon=True)
            threads.append(timer_thread)

        # Use threads for I/O-bound tasks
        blink_thread = threading.Thread(target=samuel.blinker.blink, daemon=True)
        threads.append(blink_thread)
        head_pat_thread = threading.Thread(target=samuel.head_pat, daemon=True)
        threads.append(head_pat_thread)
        look_at_me_thread = threading.Thread(target=samuel.look_at_me, daemon=True)
        threads.append(look_at_me_thread)

        # Use processes for CPU-bound tasks
        movement_process = multiprocessing.Process(
            target=Move.move, args=(move_instance,)
        )
        processes.append(movement_process)
        face_detection_process = multiprocessing.Process(
            target=FaceDetecion.face_detection_and_tracking,
            args=(face_detection_instance,),
        )
        processes.append(face_detection_process)

        for thread in threads:
            thread.start()
        for process in processes:
            process.start()

        for thread in threads:
            thread.join()
        for process in processes:
            process.join()

    except Exception as e:
        print(f"An error occurred: {e}")
        terminate_all()


if __name__ == "__main__":
    main()
