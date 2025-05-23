import os
import json
import queue
import random
import asyncio

# import pygame  # To play music
import sounddevice as sd  # replace pygame and see if it solved the competability problem with the added speech_recognition issue.
import soundfile as sf

# from mutagen.mp3 import MP3  # For mp3 files metadata
import threading
from time import sleep
import subprocess

from Servo import Movement
from global_state import Events
from multiprocessing import Lock
from config import BlinkConfig
from constants import audio_folder_path


class Speak:
    DEFAULT_GAP = 0.5

    def __init__(self, blinker=None):
        self._speaking_lock = asyncio.Lock()
        self._process_lock = Lock()
        self.events = Events()
        self.blinker = blinker

    class SoundCategories:
        class HeadPat:
            name = "head_pat"
            time_to_sleep = 1040
            queue_priority = 5

        class FaceDetectedKraa:
            name = "kraa_detect"
            time_to_sleep = 1040

        class CallFaceBackKraa:
            name = "kraa"
            queue_priority = 5

        class LookAtMe:
            name = "look_at_me"
            time_to_sleep = 740
            queue_priority = 5

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

    async def speak_worker_loop(self, audio_queue, shutdown_event):
        """
        Accept queue items in the following format:
        queue(priority, filename, gap)
        Lowest numeric priority plays first.
        """
        while not shutdown_event.is_set():
            try:
                priority, filename, gap = audio_queue.get(timeout=0.2)
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue
            # if isinstance(item, tuple):
            #     filename, gap = item
            # else:
            #     filename, gap = item, default_gap

            print(
                f"[worker] Got item from queue: {filename} (priority {priority}), sleeping after: {gap}"
            )
            await self.async_speak(filename, gap)

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
                await asyncio.gather(speak_task)
            finally:
                self.blinker.restore_blinking_time()
                self.events.speaking_event.clear()

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
        Play a WAV file and animate the servo accordingly.

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

            audio_file_path = os.path.join(audio_folder_path, audio_track_to_play)
            data, samplerate = sf.read(audio_file_path, dtype="float32")
            channels = data.shape[1] if data.ndim > 1 else 1

            # samplerate=48000
            def _play_audio():
                nonlocal data, samplerate, channels
                try:
                    with sd.OutputStream(
                        samplerate=samplerate,
                        channels=channels,
                        blocksize=0,
                        latency="low",
                    ) as stream:
                        stream.write(data)
                except Exception as e:
                    print(f"! Audio playback failed: {e}")
                    print("Attempting to reset audio system...")

                    # Restart ALSA stack
                    subprocess.run(["sudo", "alsactl", "init"], check=False)
                    # Show who's using audio devices
                    if os.path.exists("/dev/snd"):
                        fuser_output = subprocess.run(
                            ["sudo", "fuser", "-v", "/dev/snd/*"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                        print(f"🔍 fuser output:\n{fuser_output.stdout}")
                    else:
                        print("! /dev/snd/ not available — no audio devices detected.")

                    # Give it a moment to recover
                    sleep(1)

                    # Retry playback once
                    try:
                        print("🔁 Retrying playback...")
                        with sd.OutputStream(
                            samplerate=samplerate,
                            channels=channels,
                            blocksize=1024,  # 4096
                            latency="low",
                        ) as stream:
                            stream.write(data)
                    except Exception as retry_err:
                        print(f"❌ Retry failed: {retry_err}")

            # Play audio in background thread (non-blocking)
            threading.Thread(target=_play_audio, daemon=True).start()
            # How many RMS values (animation steps)
            num_frames_in_track = len(rms_dict[audio_track_to_play]["0"])

            # Calculate time per frame
            sound_duration = len(data) / samplerate
            # frame_duration = max(sound_duration / num_frames_in_track, 0.033)
            frame_duration = sound_duration / num_frames_in_track
            print(f"frame_duration: {frame_duration}")
            cluster_to_animate = random.randint(
                0, (len(rms_dict[audio_track_to_play].items()) - 2)
            )
            # Animate beak:
            previous = None
            for index, rms_values_for_servo in enumerate(
                rms_dict[audio_track_to_play][f"{cluster_to_animate}"]
            ):
                if index == (num_frames_in_track - 1):
                    print("\n\n")
                if rms_values_for_servo != previous:
                    if rms_values_for_servo == 1:
                        Movement.mouth.open(target_value=Movement.mouth.max_value)
                    else:
                        Movement.mouth.close(target_value=Movement.mouth.min_value)
                    previous = rms_values_for_servo
                await asyncio.sleep(frame_duration)

        except Exception as e:
            print(f"Error during speech: {e}")
            raise
