#import gpiozero
import RPi.GPIO as GPIO
import maestro
import time
import random
import signal
from sys import exit
import asyncio
import multiprocessing
import face_recognition
import cv2
import numpy as np
from picamera2 import Picamera2

from Servo import Mouth, HeadUpDown, HeadLeftRight, Wings, Body

from constants import Movement
from anymatron_speak import Speak
from anymatron_move import Move
from global_state import Events
from camera_face_tracking import FaceDetecion


LED_PIN = 24 # board pin no. 12
MOTION_PIN = 17 # board pin no. 11
TOUCH1_PIN = 27 # board pin no. 13
FAST_BLINK=4 # 6.7
SLOW_BLINK=23 # 33.3
# variables to save the current blink values when changing blinking rate is requested:
SAVED_FAST_BLINK = FAST_BLINK
SAVED_SLOW_BLINK = SLOW_BLINK
HEAD_GOT_PATTED = time.time()
TIME_TO_LOOK_AT_ME = 180
TIME_TO_KRAA = None


# setup:
GPIO.setmode(GPIO.BCM) # Generally set the mode for the GPIO pins
GPIO.setup(LED_PIN,GPIO.OUT) # Set the Led pin as 'out'
GPIO.output(LED_PIN,GPIO.HIGH) # Turn the led pin to high (this will turn the led 'off')
GPIO.setup(TOUCH1_PIN,GPIO.IN) # Set the touch sensor pin as 'in'
# Initiate the servo object. You can find the correct tty by running 'ls /dev/tty*' and 
# checking for new ttys before and after connecting the Pololu Maestro using USB.
maestro_controller = maestro.Controller(ttyStr='/dev/ttyACM0')


class Sensors():
    touch1 = GPIO.input(TOUCH1_PIN)
            

def signal_handler(signal, frame):
    # This function is meant to handle exit by the user (cntl+x).
    GPIO.cleanup()
    exit(0)



class Samuel:
    def wake_up():
        maestro_controller.runScriptSub(0)
        print("Samuel just Woke up! :)")

    def sleep():
        pass
        
    class Blink:
        blink_event = multiprocessing.Event()
        change_blinking_rate_event = multiprocessing.Event()
        
        def change_blinking_time(fast_blink, slow_blink):
            print("\n\nchange_blinking_time\n")
            global FAST_BLINK
            global SLOW_BLINK
            global SAVED_FAST_BLINK
            global SAVED_SLOW_BLINK
            Samuel.Blink.blink_event.set()
            Samuel.Blink.change_blinking_rate_event.set()
            FAST_BLINK = fast_blink
            SLOW_BLINK = slow_blink
            print(f"In change_blinking_time, \nSAVED_FAST_BLINK={SAVED_FAST_BLINK}\n "\
            f"SAVED_SLOW_BLINK={SAVED_SLOW_BLINK}\nFAST_BLINK={FAST_BLINK}\nSLOW_BLINK={SLOW_BLINK}")

        def restore_blinking_time():
            print("restore_blinking_time")
            global FAST_BLINK
            global SLOW_BLINK
            global SAVED_FAST_BLINK
            global SAVED_SLOW_BLINK
            Samuel.Blink.change_blinking_rate_event.wait()
            FAST_BLINK = SAVED_FAST_BLINK
            SLOW_BLINK = SAVED_SLOW_BLINK
            
        def blink():
            while True:
                blink_duration = 0.115
                GPIO.output(LED_PIN,GPIO.LOW)
                time.sleep(blink_duration)
                GPIO.output(LED_PIN,GPIO.HIGH)
                print("########### fast blink:", FAST_BLINK, "slow blink:", SLOW_BLINK)
                Samuel.Blink.blink_event.wait(random.uniform(FAST_BLINK,SLOW_BLINK))
                if Samuel.Blink.blink_event.is_set():
                    Samuel.Blink.blink_event.clear()
            GPIO.cleanup()
            
    def head_pat():
        global HEAD_GOT_PATTED
        while True:
            if GPIO.input(TOUCH1_PIN):
                Events.head_pat_event.set()
                # ~ HEAD_GOT_PATTED = time.time()
                audio_track_to_play = Speak.choose_random_sound_from_category(category=Speak.SoundCategories.HeadPat.name)
                Samuel.Blink.change_blinking_time(fast_blink=0.3, slow_blink=2.6) # blink faster
                # ~ time.sleep(random.uniform(0,0.8))
                print("Mmmmmm this feels nice!")
                process3 = multiprocessing.Process(target=asyncio.run(Speak.async_speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Speak.SoundCategories.HeadPat.time_to_sleep)))
                process3.start()
                process3.join()
                Events.head_pat_event.clear()
                Samuel.Blink.restore_blinking_time()
                HEAD_GOT_PATTED = time.time()
                print(f"\nIn head_pat, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")

        maestro_controller.close()
        GPIO.cleanup()

    def look_at_me():
        global HEAD_GOT_PATTED
        while True:
            # ~ if (current_time - HEAD_GOT_PATTED) > TIME_TO_LOOK_AT_ME and not GlobalState.SPEAKING:
            if (time.time() - HEAD_GOT_PATTED) > TIME_TO_LOOK_AT_ME and not Events.speaking_event.is_set():
                # ~ print(f"@@@@\ncurrent_time - {current_time}")
                print(f"HEAD_GOT_PATTED - {HEAD_GOT_PATTED}\n@@@@")
                # ~ GlobalState.LOOK_AT_ME = True
                Events.look_at_me_event.set()
                Samuel.Blink.change_blinking_time(fast_blink=0.5, slow_blink=3) # blink faster
                audio_track_to_play = Speak.choose_random_sound_from_category(category=Speak.SoundCategories.LookAtMe.name)
                # ~ Samuel.Speak.speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Samuel.Speak.SoundCategories.LookAtMe.time_to_sleep)
                process3 = multiprocessing.Process(target=asyncio.run(Speak.async_speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Speak.SoundCategories.LookAtMe.time_to_sleep)))
                process3.start()
                process3.join()
                HEAD_GOT_PATTED = time.time()
                print(f"\nin look_at_me, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")
                Samuel.Blink.restore_blinking_time()
                # ~ GlobalState.LOOK_AT_ME = False
                Events.look_at_me_event.clear()
    

    def load_camera():
        print("in load_camera")
        faceCascade = cv2.CascadeClassifier()
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
        picam2.start()
        while True:
            frame = picam2.capture_array()
            # ret, img = cap.read()
            # img = cv2.flip(img, -1)
            # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            resized_frame = cv2.resize(frame, (0, 0), fx=(1/4), fy=(1/4))
            flipped_frame = cv2.flip(resized_frame, 1)
            gray_resized_frame = cv2.cvtColor(flipped_frame, cv2.COLOR_BGR2GRAY)
            import ipdb; ipdb.set_trace()
            faces = faceCascade.detectMultiScale(
                gray_resized_frame,     
                scaleFactor=1.2,
                minNeighbors=5,     
                minSize=(20, 20)
            )
            for (x,y,w,h) in faces:
                cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
                roi_gray = gray_resized_frame[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
            cv2.imshow('video',frame)
            k = cv2.waitKey(30) & 0xff
            if k == 27: # press 'ESC' to quit
                break
        cap.release()
        cv2.destroyAllWindows()
    

def main():
    # Assign handler function for the user termination option (cntl+x):
    signal.signal(signal.SIGINT, signal_handler)
    print(f"\nin main, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")
    # ~ Movement.initial_position()
    # Set mouth movements to be faster:
    maestro_controller.setSpeed(chan=Movement.mouth.pin_number, speed=100)
    maestro_controller.setAccel(chan=Movement.mouth.pin_number, accel=180)
    # Faster wing movement:
    maestro_controller.setSpeed(chan=Movement.wings.pin_number, speed=20)
    maestro_controller.setAccel(chan=Movement.wings.pin_number, accel=120)
    # Set body speed and acceleration movement:
    maestro_controller.setSpeed(chan=Movement.body.pin_number, speed=10)
    maestro_controller.setAccel(chan=Movement.body.pin_number, accel=200)
    # Set head speed and acceleration movement:
    maestro_controller.setSpeed(chan=Movement.head_ud.pin_number, speed=80)
    maestro_controller.setAccel(chan=Movement.head_ud.pin_number, accel=5)
    maestro_controller.setSpeed(chan=Movement.head_rl.pin_number, speed=80)
    maestro_controller.setAccel(chan=Movement.head_rl.pin_number, accel=5)
    try:
        processes = []
        blinking_process = multiprocessing.Process(target=Samuel.Blink.blink, daemon=True)
        processes.append(blinking_process)
        head_pat_process = multiprocessing.Process(target=Samuel.head_pat)
        processes.append(head_pat_process)
        look_at_me_process = multiprocessing.Process(target=Samuel.look_at_me)
        processes.append(look_at_me_process)
        movement_process = multiprocessing.Process(target=Move.move)
        processes.append(movement_process)
        face_detection_process = multiprocessing.Process(target=FaceDetecion.face_detection_and_tracking)
        processes.append(face_detection_process)
        # ~ samuel_wake_up_thread = threading.Thread(target=Samuel.wake_up, daemon=True)
        # ~ threads.append(samuel_wake_up_thread)
        # ~ samuel_speak_thread = threading.Thread(target=Samuel.Speak.speak, daemon=True)
        # ~ threads.append(samuel_speak_thread)
        for process in processes:
            process.start()
        # This step must be taken only after starting all the processes:
        cntl_c_process = multiprocessing.Event()
        cntl_c_process.wait()
        for process in processes:
            process.join()
    except:
        for process in processes:
            process.join()
        maestro_controller.close()
        GPIO.cleanup()
        

if __name__ == "__main__":
    main()

