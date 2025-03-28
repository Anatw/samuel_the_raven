import os
import json
import random
import asyncio
import pygame  # To play music
from mutagen.mp3 import MP3  # For mp3 files metadata

from Servo import Movement
from global_state import Events
from multiprocessing import Lock
from config import BlinkConfig


audio_folder_path = "./raven_sounds/"


class Speak:
    def __init__(self, blinker=None):
        self._speaking_lock = asyncio.Lock()
        self._process_lock = Lock()
        self.events = Events()
        self.blinker = blinker

    class SoundCategories:
        class HeadPat:
            name = "head_pat"
            time_to_sleep = 1040  # When only the head_pat theread is available this should be changed to 1044

        class FaceDetectedKraa:
            name = "kraa_detect"
            time_to_sleep = 1040

        class CallFaceBackKraa:
            name = "kraa"

        class LookAtMe:
            name = "look_at_me"
            time_to_sleep = 740

        class Talking:
            name = "talking"

        class Name:
            time_to_sleep = 1040

    @staticmethod
    def choose_random_sound_from_category(category):
        with Lock():
            with open(
                os.path.join(audio_folder_path, "raven_sound_names.json")
            ) as servo_sound_names_json:
                servo_sound_names = json.load(servo_sound_names_json)
                return random.choice(servo_sound_names[category])

    async def async_speak(self, audio_track_to_play, time_to_sleep):
        """Coordinated speaking with head movement"""
        async with self._speaking_lock:  # Ensure only one speech at a time
            # if self.events.speaking_event.is_set():
            #     print("Already speaking, please wait...")
            #     return
            self.events.speaking_event.set()
            self.blinker.change_blinking_time(
                BlinkConfig.SPEAKING_FAST, BlinkConfig.SPEAKING_SLOW
            )
            try:
                # self.events.speaking_event.set()
                print(f"Starting to speak: {audio_track_to_play}")
                # head_task = asyncio.create_task(Move.move_head_rl())
                speak_task = asyncio.create_task(
                    self.speak(audio_track_to_play, time_to_sleep)
                )

                # Wait for both tasks to complete
                # await asyncio.gather(head_task, speak_task)
                await asyncio.gather(speak_task)
            finally:
                self.blinker.restore_blinking_time()
                self.events.speaking_event.clear()
        # move_head_task = Move.move_head_rl()
        # speak_task = asyncio.create_task(Speak.speak(audio_track_to_play=audio_track_to_play, time_to_sleep=time_to_sleep))
        # await asyncio.gather(speak_task, move_head_task)

    async def speak_kraa(self):
        """Periodic kraa sounds during face detection"""
        await asyncio.sleep(5)
        # every once in a while, say something:
        while Speak.events.face_detected_event.is_set():
            await asyncio.sleep(random.uniform(6, 40))
            audio_track = self.choose_random_sound_from_category(
                self.SoundCategories.FaceDetectedKraa.name
            )
            await self.async_speak(
                audio_track, self.SoundCategories.FaceDetectedKraa.time_to_sleep
            )

    async def speak(self, audio_track_to_play, time_to_sleep):
        """
        Play an mp3 music file.

        Args:
            audio_track_to_play (str): The name of the sound track to be play.
        """
        # TODO: cancel the next if and add channels, had pat is more importand than look at me - behave accordingly.
        # ~ if GlobalState.SPEAKING: # Check if audio sound is already being played:
        # if Speak.events.speaking_event.is_set(): # Check if audio sound is already being played:
        #     print("I'm bussy...\n\n")
        #     return
        # Speak.events.speaking_event.set()
        # global TALKING
        # if self.events.speaking_event.is_set():
        #     print("I'm busy...\n\n")
        #     return
        # self.events.speaking_event.set()
        try:
            with open(
                os.path.join(audio_folder_path, "servo_ready_sound_rms_dict.json")
            ) as servo_ready_rms_dict_json:
                rms_dict = json.load(servo_ready_rms_dict_json)
                # Audio file setup:
                audio_file_path = os.path.join(audio_folder_path, audio_track_to_play)
                audio = MP3(audio_file_path)
                audio_file_duration = audio.info.length
                # print(f"now playing audio file {audio_track_to_play}\n")
                print("audio_file_duration: ", audio_file_duration)
                await asyncio.sleep(1)
                pygame.mixer.init(
                    frequency=rms_dict[audio_track_to_play]["sample_rate"]
                )
                pygame.mixer.music.load(audio_file_path)
                pygame.mixer.music.play()

                # Calculate timing
                num_frames_in_track = len(rms_dict[audio_track_to_play]["0"])
                frame_duration_for_pygame_to_wait = (
                    audio_file_duration / num_frames_in_track
                )
                # Devide the length of the song to the ammount of frames, and than
                # Choose a random rms_cluster from the available range for audio_track_to_play:
                cluster_to_animate = random.randint(
                    0, (len(rms_dict[audio_track_to_play].items()) - 2)
                )
                # Animate mouth:
                for index, rms_values_for_servo in enumerate(
                    rms_dict[audio_track_to_play][f"{cluster_to_animate}"]
                ):
                    if index == (num_frames_in_track - 1):
                        print("\n\n")
                    if rms_values_for_servo == 1:
                        Movement.mouth.open(target_value=Movement.mouth.max_value)
                    else:
                        Movement.mouth.close(target_value=Movement.mouth.min_value)
                    # sleep for as long as the frame play - ideal to double by 1040
                    # pygame.time.wait(int(frame_duration_for_pygame_to_wait * time_to_sleep))
                    await asyncio.sleep(
                        frame_duration_for_pygame_to_wait * time_to_sleep / 1000
                    )

        except Exception as e:
            print(f"Error during speech: {e}")
            raise
        finally:
            pygame.quit()
