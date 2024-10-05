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
import multiprocessing
from Servo import Mouth, HeadUpDown, HeadLeftRight, Wings, Body

from utils import get_random_weighted_sleep_time


LED_PIN = 24 # board pin no. 12
MOTION_PIN = 17 # board pin no. 11
TOUCH1_PIN = 27 # board pin no. 13
audio_folder_path = "/home/anatw/samuel/raven sounds"
FAST_BLINK=4 # 6.7
SLOW_BLINK=33 # 33.3
# variables to save the current blink values when changing blinking rate is requested:
SAVED_FAST_BLINK = FAST_BLINK
SAVED_SLOW_BLINK = SLOW_BLINK
HEAD_GOT_PATTED = time.time()
SPEAKING = False
LOOK_AT_ME = False
HEAD_PAT = False
TIME_TO_LOOK_AT_ME = 60
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
    

class Movement():
    mouth = Mouth(
        pin_number=0,
        min_value=6200,
        max_value=9250,
        gesticulation_repetition=1
    )
    # For head up-down movement, lower numbers will turn down, higher numbers will turn up:
    head_ud = HeadUpDown(
        pin_number=1,
        min_value=4450,
        max_value=8400,
        gesticulation_repetition=4
    )
    head_rl = HeadLeftRight(
        pin_number=2,
        min_value=3300,
        max_value=7100,
        gesticulation_repetition=5
    )
    wings = Wings(
        pin_number=3,
        min_value=4600,
        max_value=5750,
        gesticulation_repetition=3
    )
    body = Body(
        pin_number=4,
        min_value=5000,
        max_value=6200,
        gesticulation_repetition=2
    )
            

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
        blink_event = threading.Event()
        change_blinking_rate_event = threading.Event()
            
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
        
    class Speak:
        class SoundCategories:
            class HeadPat:
                name = "head_pat"
                time_to_sleep = 218 # When only the head_pat theread is available this should be changed to 1044
            
            class Kraa:
                name = "kraa"
            
            class LookAtMe:
                name = "look_at_me"
                time_to_sleep = -0.008
            
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
                audio_track_to_play (str): The name of the sound track to be play.
            """
            global SPEAKING
            # TODO: cancel the next if and add channels, had pat is more importand than look at me - behave accordingly.
            if SPEAKING: # Check if audio sound is already being played:
                print("I'm bussy...\n\n")
                return
            SPEAKING = True         
            global TALKING
            with open(os.path.join(audio_folder_path, "servo_ready_sound_rms_dict.json")) as servo_ready_rms_dict_json:
                rms_dict = json.load(servo_ready_rms_dict_json)
                # Play the audio file:
                audio_file_path = os.path.join(audio_folder_path, audio_track_to_play)
                audio = MP3(audio_file_path)
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
                    if index == (num_frames_in_track - 1):
                        print("\n\n\n\n\n\n\n\n")
                    if rms_values_for_servo == 1:
                        Movement.mouth.open(target_value=Movement.mouth.max_value)
                    else:
                        Movement.mouth.close(target_value=Movement.mouth.min_value)
                    # sleep for as long as the frame play - ideal to double by 1040
                    pygame.time.wait(int(frame_duration_for_pygame_to_wait * time_to_sleep))

                timer_end = time.time()
                time_passed = timer_end - timer_start
                print(f"time passed: \n{time_passed}\naudio_file_duration: \n {audio_file_duration}")
                pygame.quit()
                SPEAKING = False
            return

    def head_pat():
        global HEAD_GOT_PATTED
        global HEAD_PAT
        while True:
            if GPIO.input(TOUCH1_PIN):
                HEAD_PAT = True
                HEAD_GOT_PATTED = time.time()
                audio_track_to_play = Samuel.Speak.choose_random_sound_from_category(category=Samuel.Speak.SoundCategories.HeadPat.name)
                Samuel.Blink.change_blinking_time(fast_blink=0.3, slow_blink=2.6) # blink faster
                # ~ time.sleep(random.uniform(0,0.8))
                print("Mmmmmm this feels nice!")
                Samuel.Speak.speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Samuel.Speak.SoundCategories.HeadPat.time_to_sleep)
                HEAD_PAT = False
                Samuel.Blink.restore_blinking_time()
                HEAD_GOT_PATTED = time.time()
                print(f"\nIn head_pat, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")

        maestro_controller.close()
        GPIO.cleanup()
    
    def look_at_me():
        global HEAD_GOT_PATTED
        global LOOK_AT_ME
        while True:
            current_time = time.time()
            if (current_time - HEAD_GOT_PATTED) > TIME_TO_LOOK_AT_ME and not SPEAKING:
                LOOK_AT_ME = True
                Samuel.Blink.change_blinking_time(fast_blink=0.5, slow_blink=3) # blink faster
                audio_track_to_play = Samuel.Speak.choose_random_sound_from_category(category=Samuel.Speak.SoundCategories.LookAtMe.name)
                Samuel.Speak.speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Samuel.Speak.SoundCategories.LookAtMe.time_to_sleep)
                HEAD_GOT_PATTED = time.time()
                print(f"\nin look_at_me, HEAD_GOT_PATTED: {HEAD_GOT_PATTED}\n")
                Samuel.Blink.restore_blinking_time()
                LOOK_AT_ME = False
                
    class Move:
        movements = {
            11: "Movement.head_rl.move_right()",
            12: "Movement.head_rl.move_left()",
            21: "Movement.head_ud.move_up()",
            22: "Movement.head_ud.move_down()",
            31: "Movement.body.move_up()",
            32: "Movement.body.move_down()",
            41: "Movement.wings.move_up()",
            42: "Movement.wings.move_down()",
        }
        movements_keys = list(movements.keys())
        
        # gesticulation
        async def move_wings():
            print("move_wings")
            Movement.wings.move_up()
            await asyncio.sleep(random.uniform(0.5,1.2))
            Movement.wings.move_down()

        async def move_head_rl():
            print("move_head_rl")
            Movement.head_rl.move_right()
            await asyncio.sleep(random.uniform(0.5,1.2))
            Movement.head_rl.move_left()
           
        async def move_head_ud():
            print("move_head_ud")
            Movement.head_ud.move_down()
            await asyncio.sleep(random.uniform(0.5,1.2))
            Movement.head_ud.move_up()
            
        async def move_body():
            print("move_head_ud")
            Movement.body.move_up()
            await asyncio.sleep(random.uniform(0.5,1.2))
            Movement.body.move_down()
            
        async def async_move():
            await asyncio.gather(
                Samuel.Move.move_wings(),
                Samuel.Move.move_head_rl(),
                Samuel.Move.move_head_ud(),
                Samuel.Move.move_body(),
            )
        
        def get_random_duo_combination():
            first_number = random.choice(Samuel.Move.movements_keys)
            first_digit = first_number // 10
            # Create a list of numbers that do not start with the first digit
            remaining_numbers = [number for number in Samuel.Move.movements_keys if number // 10 != first_digit]
            second_number = random.choice(remaining_numbers)
            return Samuel.Move.movements[first_number], Samuel.Move.movements[second_number]
        
        async def random_async_move():
            random_duo_combination = Samuel.Move.get_random_duo_combination()
            exec(random_duo_combination[0])
            exec(random_duo_combination[1])
                
        def move():
            # This thread allow Samuel to move while doing other routines such as speaking. The movement is always available in the background.
            should_start_movement_cycle = True
            while True:
                if should_start_movement_cycle:
                    starting_time = time.time()
                    random_time_to_sleep = get_random_weighted_sleep_time()
                    print(f"random_time_to_sleep = {random_time_to_sleep}")
                    should_start_movement_cycle = False
                if LOOK_AT_ME:
                   process1 = multiprocessing.Process(target=asyncio.run(Samuel.Move.async_move()))
                   process1.start()
                   process1.join()
                if HEAD_PAT:
                    print("!!!!!!!! In move, head got patted")
                    Movement.body.move_down()
                    Movement.head_ud.move_up()
                    time.sleep(random.uniform(0.5,1.2))
                    Movement.head_rl.move_right()                
                    Movement.body.move_up(Movement.body.mid_value)
                    Movement.head_ud.move_down()
                    Movement.head_rl.move_left()
                if not (HEAD_PAT or LOOK_AT_ME) and time.time() >= starting_time + random_time_to_sleep:
                    print("!!! In move() if time has come to strech")
                    process2 = multiprocessing.Process(target=asyncio.run(Samuel.Move.random_async_move()))
                    process2.start()
                    process2.join()
                    should_start_movement_cycle = True
    
    
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
    maestro_controller.setAccel(chan=Movement.mouth.pin_number, accel=120)
    try:
        threads = []
        blinking_thread = threading.Thread(target=Samuel.Blink.blink, daemon=True)
        threads.append(blinking_thread)
        head_pat_thread = threading.Thread(target=Samuel.head_pat, daemon=True)
        threads.append(head_pat_thread)
        look_at_me_thread = threading.Thread(target=Samuel.look_at_me, daemon=True)
        threads.append(look_at_me_thread)
        movement_thread = threading.Thread(target=Samuel.Move.move, daemon=True)
        threads.append(movement_thread)
        # ~ samuel_wake_up_thread = threading.Thread(target=Samuel.wake_up, daemon=True)
        # ~ threads.append(samuel_wake_up_thread)
        # ~ samuel_speak_thread = threading.Thread(target=Samuel.Speak.speak, daemon=True)
        # ~ threads.append(samuel_speak_thread)
        for thread in threads:
            thread.start()
        # This step must be taken only after starting all the threads:
        cntl_c_thread = threading.Event()
        cntl_c_thread.wait()
        for thread in threads:
            thread.join()
    except:
        for thread in threads:
            thread.join()
        maestro_controller.close()
        GPIO.cleanup()
        

if __name__ == "__main__":
    main()
