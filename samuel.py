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


LED_PIN = 24 # board pin no. 12
MOTION_PIN = 17 # board pin no. 11
TOUCH1_PIN = 27 # board pin no. 13
# ~ test_sound = "/home/anatw/samuel/raven-call-72946.mp3"
audio_folder_path = "/home/anatw/samuel/raven sounds"


# setup:
GPIO.setmode(GPIO.BCM) # Generally set the mode for the GPIO pins
GPIO.setup(LED_PIN,GPIO.OUT) # Set the Led pin as 'out'
GPIO.output(LED_PIN,GPIO.HIGH) # Turn the led pin to high (this will turn the led 'off')
GPIO.setup(TOUCH1_PIN,GPIO.IN) # Set the touch sensor pin as 'in'
# Initiate the servo object. You can find the correct tty by running 'ls /dev/tty*' and 
# checking for new ttys before and after connecting the Pololu Maestro using USB.
maestro_controller = maestro.Controller(ttyStr='/dev/ttyACM0')
# Initiate the pygame module:


class sensors():
    touch1 = GPIO.input(TOUCH1_PIN)


def signal_handler(signal, frame):
    # This function is meant to handle exit by the user (cntl+x).
    GPIO.cleanup()
    exit(0)


def blink():
    #time.sleep(random.uniform(6.7, 33.3))
    while True:
        blink_time = 0.115
        time.sleep(random.uniform(1,3))
        GPIO.output(LED_PIN,GPIO.LOW)
        time.sleep(blink_time)
        GPIO.output(LED_PIN,GPIO.HIGH)
        time.sleep(blink_time)
        # ~ print("blinking")

    GPIO.cleanup()


def head_pat():
    # TODO: should blink more often when head is patted.
    while True:
        head_pat = "head_pat"
        audio_track_to_play = Samuel.Speak.choose_random_sound_from_category(category=head_pat)
        if GPIO.input(TOUCH1_PIN):
            maestro_controller.setAccel(1,4)
            maestro_controller.setTarget(1,5700)
            print("Mmmmmm this feels nice!")
            Samuel.Speak.speak(audio_track_to_play=audio_track_to_play)
            time.sleep(0.5)
            maestro_controller.setTarget(1,4000)

    maestro_controller.close()
    GPIO.cleanup()
    

class Samuel:
    def wake_up():
        maestro_controller.runScriptSub(0)
        print("Samuel just Woke up! :)")

    def sleep():
        pass
    
    class Speak:
        sound_categories = [
            "head_pat",
            "kraa",
            "look_at_me",
            "talking",
        ]
        
        def choose_random_sound_from_category(category):
            with open(os.path.join(audio_folder_path, "raven_sound_names.json")) as servo_sound_names_json:
                servo_sound_names = json.load(servo_sound_names_json)
                return random.choice(servo_sound_names[category])
                # ~ audio_track_to_play ="/home/anatw/samuel/raven sounds/head_pat7.mp3"
        def speak(audio_track_to_play):
            """
            Play an mp3 music file.
            
            Args:
                audio_track_path (strhigher quality): Path to the music track you want to play.
            """
            maestro_controller.setAccel(0,50)
            # ~ random_category = random.choice(Samuel.Speak.sound_categories)
            # ~ audio_track_to_play = Samuel.Speak.choose_random_sound_from_category(category=random_category)
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
                # Choose a random rms_cluster from the available range for the played audio track:
                cluster_to_animate = random.randint(0,(len(rms_dict[audio_track_to_play].items())-2))
                for index, rms_values_for_servo in enumerate(rms_dict[audio_track_to_play][f"{cluster_to_animate}"]):
                    # ~ import ipdb; ipdb.set_trace()
                    if index == (num_frames_in_track - 1):
                        print("\n\n\n\n\n\n\n\n")
                    if rms_values_for_servo == 1:
                        maestro_controller.setTarget(0,9250)
                    else:
                        # ~ print("naa...")
                        maestro_controller.setTarget(0,6300)
                    pygame.time.wait(int(frame_duration_for_pygame_to_wait * 950)) # sleep for as long as the frame play - ideal to double by 1040

                timer_end = time.time()
                time_passed = timer_end - timer_start
                print(f"time passed: \n{time_passed}\naudio_file_duration: \n {audio_file_duration}")
                # ~ if time_passed < audio_file_duration:
                    # ~ raise
                pygame.quit()
            return

        
    
def main():
    # Assign handler function for the user termination option (cntl +x):
    signal.signal(signal.SIGINT, signal_handler)
    try:
        threads = []
        blinking_thread = threading.Thread(target=blink, daemon=True)
        threads.append(blinking_thread)
        head_pat_thread = threading.Thread(target=head_pat, daemon=True)
        threads.append(head_pat_thread)
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
