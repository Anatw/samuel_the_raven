import os
import json
import random
import asyncio
import time
import pygame # To play music
from mutagen.mp3 import MP3 # For mp3 files metadata
from mutagen.wave import WAVE # For mp3 files metadata

from constants import Movement
from global_state import Events


audio_folder_path = "/home/anatw/samuel/raven sounds"

    
class Speak:
    class SoundCategories:
        class HeadPat:
            name = "head_pat"
            time_to_sleep = 1040 # When only the head_pat theread is available this should be changed to 1044
        
        class Kraa:
            name = "kraa"
        
        class LookAtMe:
            name = "look_at_me"
            time_to_sleep = 740
        
        class Talking:
            name = "talking"
    
    def choose_random_sound_from_category(category):
        with open(os.path.join(audio_folder_path, "raven_sound_names.json")) as servo_sound_names_json:
            servo_sound_names = json.load(servo_sound_names_json)
            return random.choice(servo_sound_names[category])
    
    async def async_speak(audio_track_to_play, time_to_sleep):
        task = asyncio.create_task(Speak.speak(audio_track_to_play=audio_track_to_play, time_to_sleep=Speak.SoundCategories.HeadPat.time_to_sleep))
        await task
        
    async def speak(audio_track_to_play, time_to_sleep):
        """
        Play an mp3 music file.
        
        Args:
            audio_track_to_play (str): The name of the sound track to be play.
        """
        # TODO: cancel the next if and add channels, had pat is more importand than look at me - behave accordingly.
        # ~ if GlobalState.SPEAKING: # Check if audio sound is already being played:
        if Events.speaking_event.is_set(): # Check if audio sound is already being played:
            print("I'm bussy...\n\n")
            return
        Events.speaking_event.set()
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
            Events.speaking_event.clear()
        return
