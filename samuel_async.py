# import gpiozero
import RPi.GPIO as GPIO
import time
import random
import asyncio

from animatron_speak import Speak
from global_state import Events
from config import BlinkConfig
import threading


LED_PIN = 24  # board pin no. 12
MOTION_PIN = 17  # board pin no. 11
TOUCH1_PIN = 27  # board pin no. 13
TIME_TO_KRAA = None


class Samuel:
    def __init__(self):
        self.gpio_setup()
        self.blinker = self.Blink()
        self.speaker = Speak(blinker=self.blinker)
        self.events = Events()
        self.head_patted_time = time.time()
        self.time_to_look_at_me = 180
        self.audio_lock = threading.Lock()  # lock for audio playback

    @staticmethod
    def gpio_setup():
        GPIO.setmode(GPIO.BCM)  # Generally set the mode for the GPIO pins
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(
            LED_PIN, GPIO.HIGH
        )  # Turn the led pin to high (this will turn the led 'off')
        GPIO.setup(TOUCH1_PIN, GPIO.IN)  # Set the touch sensor pin as 'in'

    class Blink:
        _instance = None

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.lock = threading.Lock()
                cls._instance.config = BlinkConfig()
                cls._instance.events = Events()
                print(
                    f"BlinkConfig initialized with fast: {cls._instance.config.fast}, slow: {cls._instance.config.slow}"
                )
            return cls._instance

        def change_blinking_time(self, fast_blink, slow_blink):
            """Change blinking time in a thread safe manner"""
            with self.lock:
                self.config.set_blink_rate(fast_blink, slow_blink)
            self.events.blink_event.set()

        def restore_blinking_time(self):
            with self.lock:
                self.config.set_blink_rate(
                    self.config.DEFAULT_FAST, self.config.DEFAULT_SLOW
                )
            self.events.blink_event.set()

        def blink(self):
            while True:
                GPIO.output(LED_PIN, GPIO.LOW)
                time.sleep(BlinkConfig.BLINK_DURATION)
                GPIO.output(LED_PIN, GPIO.HIGH)

                with self.lock:
                    current_fast = self.config.fast
                    current_slow = self.config.slow

                time_to_wait_between_blinks = random.uniform(current_fast, current_slow)
                if self.events.blink_event.wait(timeout=time_to_wait_between_blinks):
                    self.events.blink_event.clear()

    def play_audio(self, audio_track, time_to_sleep):
        with self.audio_lock:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.speaker.async_speak(audio_track, time_to_sleep)
            )

    def head_pat(self):
        while True:
            if GPIO.input(TOUCH1_PIN):
                self.events.head_pat_event.set()  # For use inside animatron_move
                audio_track_to_play = Speak.choose_random_sound_from_category(
                    category=Speak.SoundCategories.HeadPat.name
                )
                self.blinker.change_blinking_time(
                    BlinkConfig.PATTED_FAST, BlinkConfig.PATTED_SLOW
                )
                print("Mmmmmm this feels nice!")
                self.play_audio(
                    audio_track_to_play, Speak.SoundCategories.HeadPat.time_to_sleep
                )
                self.events.head_pat_event.clear()
                self.blinker.restore_blinking_time()
                self.head_patted_time = time.time()

    def look_at_me(self):
        while True:
            if (
                time.time() - self.head_patted_time
            ) > self.time_to_look_at_me and not self.events.speaking_event.is_set():
                self.events.look_at_me_event.set()
                self.blinker.change_blinking_time(
                    fast_blink=BlinkConfig.ATTENTION_FAST,
                    slow_blink=BlinkConfig.ATTENTION_SLOW,
                )
                audio_track_to_play = Speak.choose_random_sound_from_category(
                    category=Speak.SoundCategories.LookAtMe.name
                )
                self.play_audio(
                    audio_track_to_play, Speak.SoundCategories.LookAtMe.time_to_sleep
                )
                self.head_patted_time = time.time()
                self.blinker.restore_blinking_time()
                self.events.look_at_me_event.clear()
