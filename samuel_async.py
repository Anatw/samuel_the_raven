# import gpiozero
import RPi.GPIO as GPIO
import time
import random

from animatron_speak import Speak
from global_state import Events
from config import BlinkConfig
import threading


LED_PIN = 24  # board pin no. 12
MOTION_PIN = 17  # board pin no. 11
TOUCH1_PIN = 27  # board pin no. 13
TIME_TO_KRAA = None


class Samuel:
    def __init__(self, speech_queue):
        self.gpio_setup()
        self.blinker = self.Blink()
        self.speaker = Speak(blinker=self.blinker, speech_queue=speech_queue)
        self.events = Events()
        self.head_patted_time = time.time()
        self.time_to_look_at_me = 10
        self.audio_lock = threading.Lock()  # lock for audio playback
        self.speech_queue = speech_queue

    @staticmethod
    def handle_touch(channel):
        print("Mmmmmm this feels nice")

    @staticmethod
    def gpio_setup():
        GPIO.setmode(GPIO.BCM)  # Generally set the mode for the GPIO pins
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(
            LED_PIN, GPIO.HIGH
        )  # Turn the led pin to high (this will turn the led 'off')
        # GPIO.setup(TOUCH1_PIN, GPIO.IN)  # Set the touch sensor pin as 'in'
        GPIO.setup(TOUCH1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Register touch detection with debounce
        GPIO.add_event_detect(
            TOUCH1_PIN, GPIO.RISING, callback=Samuel.handle_touch, bouncetime=300
        )

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
        # with self.audio_lock:
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)
        #     loop.run_until_complete(
        #         self.speaker.async_speak(audio_track, time_to_sleep)
        #     )
        self.speech_queue.put(
            {"type": "speak", "track": audio_track, "time_to_sleep": time_to_sleep}
        )

    def head_pat(self):
        def _is_touch_confirmed(pin, duration=0.1, checks=5):
            confirmed = 0
            for _ in range(checks):
                if GPIO.input(pin):
                    confirmed += 1
                time.sleep(duration / checks)
            return confirmed == checks

        while True:
            if _is_touch_confirmed(TOUCH1_PIN):
                self.events.head_pat_event.set()  # For use inside animatron_move
                audio_track_to_play = Speak.choose_random_sound_from_category(
                    category=Speak.SoundCategories.HeadPat.name
                )
                self.blinker.change_blinking_time(
                    BlinkConfig.PATTED_FAST, BlinkConfig.PATTED_SLOW
                )

                self.speaker.speech_queue.put(
                    {
                        "type": "speak",
                        "track": audio_track_to_play,
                        "sleep": Speak.SoundCategories.HeadPat.time_to_sleep,
                    }
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

                self.speaker.speech_queue.put(
                    {
                        "type": "speak",
                        "track": audio_track_to_play,
                        "sleep": Speak.SoundCategories.LookAtMe.time_to_sleep,
                    }
                )

                self.head_patted_time = time.time()
                self.blinker.restore_blinking_time()
                self.events.look_at_me_event.clear()
