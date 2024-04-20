#import gpiozero
import RPi.GPIO as GPIO
import maestro
import time
import random
import threading
import signal
import pygame # To play music
from mutagen.mp3 import MP3 # For mp3 files metadata
from mutagen.wave import WAVE # For mp3 files metadata
from sys import exit
import os
import json
import struct
import asyncio
from Servo import Mouth, HeadUpDown, HeadLeftRight, Wings, Body


LED_PIN = 24 # board pin no. 12
MOTION_PIN = 17 # board pin no. 11
TOUCH1_PIN = 27 # board pin no. 13
audio_folder_path = "/home/anatw/samuel/raven sounds"
FAST_BLINK=4 # 6.7
SLOW_BLINK=33 # 33.3
# variables to save the current blink values when changing blinking rate is requested:
<<<<<<< HEAD
SAVED_FAST_BLINK = FAST_BLINK
SAVED_SLOW_BLINK = SLOW_BLINK
HEAD_GOT_PATTED = time.time()
SPEAKING = False
LOOK_AT_ME = False
HEAD_PAT = False
TIME_TO_LOOK_AT_ME = 3
=======
SAVED_FAST_BLINK = None
SAVED_SLOW_BLINK = None
HEAD_GOT_PATTED = time.time()
TALKING = False
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7


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
    

class Movement():
    mouth = Mouth(pin_number=0, min_value=6200, max_value=9250)
    # For head up-down movement, lower numbers will turn down, higher numbers will turn up:
    head_ud = HeadUpDown(pin_number=1, min_value=4450, max_value=8400)
    head_rl = HeadLeftRight(pin_number=2, min_value=3300, max_value=7100)
    wings = Wings(pin_number=3, min_value=4600, max_value=5750)
    body = Body(pin_number=4, min_value=5000, max_value=6200)
    
    # ~ def initial_position():
        # ~ # setting all the servoes to the initial value so that they alway know their current position value.
        # ~ Movement.mouth.move(target_value=Movement.mouth.min_value)
        # ~ Movement.head_ud.move(target_value=Movement.head_ud.mid_value)
        # ~ Movement.head_rl.move(target_value=Movement.head_rl.mid_value)
        # ~ Movement.wings.move(target_value=Movement.wings.mid_value)
        # ~ Movement.body.move(target_value=Movement.body.mid_value)
            

def signal_handler(signal, frame):
    # This function is meant to handle exit by the user (cntl+x).
    GPIO.cleanup()
<<<<<<< HEAD
    exit(0)


def head_pat():
    # TODO: count time from last head_pat. If greater than X, play a look_at_me sound.
    while True:
        head_pat = "head_pat"
        audio_track_to_play = Samuel.Speak.choose_random_sound_from_category(category=head_pat)
        if GPIO.input(TOUCH1_PIN):
            # ~ maestro_controller.setAccel(1,4)
            # ~ Movement.wings.move_down()
            time.sleep(random.uniform(0,0.8))
            Movement.body.move_down()
            Movement.head_ud.move_up()
            # ~ maestro_controller.setTarget(1,5700)
            print("Mmmmmm this feels nice!")
            Samuel.Speak.speak(audio_track_to_play=audio_track_to_play)
            time.sleep(0.5)
            # ~ maestro_controller.setTarget(1,4000)
            Movement.body.move_up()
            Movement.head_ud.move_down()

    maestro_controller.close()
    GPIO.cleanup()
=======
    exit(0)  
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7


class Samuel:
    def wake_up():
        maestro_controller.runScriptSub(0)
        print("Samuel just Woke up! :)")

    def sleep():
        pass
        
    class Blink:
        def change_blinking_time(fast_blink, slow_blink):
            print("change_blinking_time")
            global FAST_BLINK
            global SLOW_BLINK
            global SAVED_FAST_BLINK
            global SAVED_SLOW_BLINK
            # ~ if fast_blink != FAST_BLINK or slow_blink != SLOW_BLINK:
            SAVED_FAST_BLINK = FAST_BLINK
            SAVED_SLOW_BLINK = SLOW_BLINK
            FAST_BLINK = fast_blink
            SLOW_BLINK = slow_blink
            # ~ # If the blinking time has already changed - don't change the saved values
            # ~ if SAVED_FAST_BLINK or SAVED_SLOW_BLINK:
                # ~ return

            print(f"In change_blinking_time, \nSAVED_FAST_BLINK={SAVED_FAST_BLINK}\n "\
            f"SAVED_SLOW_BLINK={SAVED_SLOW_BLINK}\nFAST_BLINK={FAST_BLINK}\nSLOW_BLINK={SLOW_BLINK}")

            
        def restore_blinking_time():
            print("restore_blinking_time")
            global FAST_BLINK
            global SLOW_BLINK
            global SAVED_FAST_BLINK
            global SAVED_SLOW_BLINK
            FAST_BLINK = SAVED_FAST_BLINK
            SLOW_BLINK = SAVED_SLOW_BLINK
            SAVED_FAST_BLINK = None
            SAVED_SLOW_BLINK = None
            
        def blink():
            while True:
                blink_duration = 0.115
                time.sleep(random.uniform(FAST_BLINK,SLOW_BLINK)) #time.sleep(random.uniform(6.7, 33.3))
                print("fast blink:", FAST_BLINK, "slow blink:", SLOW_BLINK)
                GPIO.output(LED_PIN,GPIO.LOW)
                time.sleep(blink_duration)
                GPIO.output(LED_PIN,GPIO.HIGH)
                # time.sleep(blink_duration)
                # ~ print("blinking")

            GPIO.cleanup()
        
    class Speak:
        class SoundCategories:
            class HeadPat:
                name = "head_pat"
<<<<<<< HEAD
                time_to_sleep = 1
=======
                time_to_sleep = 550
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7
            
            class Kraa:
                name = "kraa"
            
            class LookAtMe:
                name = "look_at_me"
<<<<<<< HEAD
                time_to_sleep = 0.1
=======
                time_to_sleep = 10
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7
            
            class Talking:
                name = "talking"
        
        def choose_random_sound_from_category(category):
            with open(os.path.join(audio_folder_path, "raven_sound_names.json")) as servo_sound_names_json:
                servo_sound_names = json.load(servo_sound_names_json)
                return random.choice(servo_sound_names[category])
                
        def speak(audio_track_to_play, time_to_sleep):
            """
            Play an mp3 music file.
            
            Args:
                audio_track_to_play (str): The name of the music track to be play.
            """
<<<<<<< HEAD
            global SPEAKING
            # TODO: cancel the next if and add channels, had pat is more importand than look at me - behave accordingly.
            if SPEAKING: # Check if audio sound is already being played:
                print("I'm bussy...\n\n")
                return
            SPEAKING = True         
=======
            global TALKING
            # TODo: cancel the next if and add channels, had pat is more importand than look at me - behave accordingly.
            if TALKING: # Check if audio sound is already being played:
                print("I'm bussy...\n\n")
                return
            TALKING = True
            maestro_controller.setAccel(0,50)
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7
            # ~ Samuel.Blink.change_blinking_time(fast_blink=1, slow_blink=3) # blink faster
            # Lower body and raise head:
            with open(os.path.join(audio_folder_path, "servo_ready_sound_rms_dict.json")) as servo_ready_rms_dict_json:
                rms_dict = json.load(servo_ready_rms_dict_json)
                # Play the audio file:
                audio_file_path = os.path.join(audio_folder_path, audio_track_to_play)
                audio = MP3(audio_file_path)
                # ~ sample_width = 16
                audio_file_duration = audio.info.length
                print(f"now playing audio file {audio_track_to_play}\n")
                print("audio_file_duration: ", audio_file_duration)
                time.sleep(1)
                pygame.mixer.init(frequency=rms_dict[audio_track_to_play]['sample_rate'])
                pygame.mixer.music.load(audio_file_path)
                timer_start = time.time()
                pygame.mixer.music.play()
                num_frames_in_track = len(rms_dict[audio_track_to_play]["0"])
                print(f"rms_dict[audio_track_to_play]: {num_frames_in_track}")
                frame_duration_for_pygame_to_wait = (audio_file_duration / num_frames_in_track)
                print("frame_duration", frame_duration_for_pygame_to_wait)
                # Devide the length of the song to the ammount of frames, and than 
                # Choose a random rms_cluster from the available range for audio_track_to_play:
                cluster_to_animate = random.randint(0,(len(rms_dict[audio_track_to_play].items())-2))
                print(f"Cluster choosen for animation: {cluster_to_animate}")
                for index, rms_values_for_servo in enumerate(rms_dict[audio_track_to_play][f"{cluster_to_animate}"]):
                    # ~ import ipdb; ipdb.set_trace()
                    if index == (num_frames_in_track - 1):
                        print("\n\n\n\n\n\n\n\n")
                    if rms_values_for_servo == 1:
                        Movement.mouth.open(target_value=Movement.mouth.max_value)
                    else:
                        # ~ print("naa...")
                        Movement.mouth.close(target_value=Movement.mouth.min_value)
                    pygame.time.wait(int(frame_duration_for_pygame_to_wait * time_to_sleep)) # sleep for as long as the frame play - ideal to double by 1040

                timer_end = time.time()
                time_passed = timer_end - timer_start
                print(f"time passed: \n{time_passed}\naudio_file_duration: \n {audio_file_duration}")
                # ~ if time_passed < audio_file_duration:
                    # ~ raise
                pygame.quit()
                TALKING = False
                # ~ Samuel.Blink.restore_blinking_time()
            return

<<<<<<< HEAD
                SPEAKING = False
                # ~ Samuel.Blink.restore_blinking_time()
            return

    def head_pat():
        global HEAD_GOT_PATTED
        global HEAD_PAT
        while True:
            if GPIO.input(TOUCH1_PIN):
                HEAD_PAT = True
                HEAD_GOT_PATTED = time.time()
                audio_track_to_play = Samuel.Speak.choose_random_sound_from_category(category=Samuel.Speak.SoundCategories.HeadPat.name)
                Samuel.Blink.change_blinking_time(fast_blink=0, slow_blink=2) # blink faster
                # ~ time.sleep(random.uniform(0,0.8))
                print("Mmmmmm this feels nice!")
                Samuel.Speak.speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Samuel.Speak.SoundCategories.HeadPat.time_to_sleep)
                HEAD_PAT = False
                Samuel.Blink.restore_blinking_time()
                HEAD_GOT_PATTED = time.time()
                print(f"\nin head_pat, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")
=======
    def head_pat():
        global HEAD_GOT_PATTED
        global TALKING
        while True:
            if GPIO.input(TOUCH1_PIN):
                # ~ TALKING = True
                audio_track_to_play = Samuel.Speak.choose_random_sound_from_category(category=Samuel.Speak.SoundCategories.HeadPat.name)
                Samuel.Blink.change_blinking_time(fast_blink=0, slow_blink=2) # blink faster
                # ~ maestro_controller.setAccel(1,4)
                # ~ Movement.wings.move_down()
                # ~ time.sleep(random.uniform(0,0.8))
                Movement.body.move_down()
                Movement.head_ud.move_up()
                # ~ maestro_controller.setTarget(1,5700)
                print("Mmmmmm this feels nice!")
                Samuel.Speak.speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Samuel.Speak.SoundCategories.HeadPat.time_to_sleep)
                time.sleep(random.uniform(0.5,1.2))
                # ~ maestro_controller.setTarget(1,4000)
                Movement.body.move_up(Movement.body.mid_value)
                Movement.head_ud.move_down()
                HEAD_GOT_PATTED = time.time()
                print(f"\nin head_pat, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")
                Samuel.Blink.restore_blinking_time()

>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7
        maestro_controller.close()
        GPIO.cleanup()
    
    def look_at_me():
        global HEAD_GOT_PATTED
<<<<<<< HEAD
        global LOOK_AT_ME
        while True:
            current_time = time.time()
            if (current_time - HEAD_GOT_PATTED) > TIME_TO_LOOK_AT_ME and not SPEAKING:
                LOOK_AT_ME = True
=======
        while True:
            current_time = time.time()
            if (current_time - HEAD_GOT_PATTED) > 3 and not TALKING:
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7
                audio_track_to_play = Samuel.Speak.choose_random_sound_from_category(category=Samuel.Speak.SoundCategories.LookAtMe.name)
                Samuel.Speak.speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Samuel.Speak.SoundCategories.LookAtMe.time_to_sleep)
                HEAD_GOT_PATTED = time.time()
                print(f"\nin look_at_me, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")
<<<<<<< HEAD
                LOOK_AT_ME = False
    
    def move():
        # This thread allow Samuel to move while doin other routines such as speaking. The movement is always available in the background.
        while True:
            if LOOK_AT_ME:
                Movement.wings.wave()
            if HEAD_PAT:
                print("!!!!!!!! In move, head got patted")
                Movement.body.move_down()
                Movement.head_ud.move_up()
                time.sleep(random.uniform(0.5,1.2))                
                Movement.body.move_up(Movement.body.mid_value)
                Movement.head_ud.move_down()
=======
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7
        
    
def main():
    # Assign handler function for the user termination option (cntl+x):
    signal.signal(signal.SIGINT, signal_handler)
    print(f"\nin main, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")
    # ~ Movement.initial_position()
<<<<<<< HEAD
    # Set mouth movements to be faster:
    maestro_controller.setSpeed(chan=Movement.mouth.pin_number, speed=100)
    maestro_controller.setAccel(chan=Movement.mouth.pin_number, accel=180)
    # Faster wing movement:
    maestro_controller.setSpeed(chan=Movement.wings.pin_number, speed=150)
    maestro_controller.setAccel(chan=Movement.mouth.pin_number, accel=20)
=======
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7
    try:
        threads = []
        blinking_thread = threading.Thread(target=Samuel.Blink.blink, daemon=True)
        threads.append(blinking_thread)
        head_pat_thread = threading.Thread(target=Samuel.head_pat, daemon=True)
        threads.append(head_pat_thread)
        look_at_me_thread = threading.Thread(target=Samuel.look_at_me, daemon=True)
        threads.append(look_at_me_thread)
<<<<<<< HEAD
        movement_thread = threading.Thread(target=Samuel.move, daemon=True)
        threads.append(movement_thread)
=======
>>>>>>> a2b33287222d40463b5f8b8b94ef9b0f13d39da7
        # ~ samuel_wake_up_thread = threading.Thread(target=Samuel.wake_up, daemon=True)
        # ~ threads.append(samuel_wake_up_thread)
        # ~ samuel_speak_thread = threading.Thread(target=Samuel.Speak.speak, daemon=True)
        # ~ threads.append(samuel_speak_thread)
        print("1")
        for thread in threads:
            thread.start()
        # This step must be taken only after starting all the threads:
        cntl_c_thread = threading.Event()
        cntl_c_thread.wait()
        print("2")
        for thread in threads:
            thread.join()
        print("3")
    except:
        for thread in threads:
            thread.join()
        maestro_controller.close()
        GPIO.cleanup()
        

if __name__ == "__main__":
    main()
