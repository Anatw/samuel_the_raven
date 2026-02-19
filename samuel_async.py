from gpiozero import LED
import time
import random

from animatron_speak import Speak
from global_state import Events
from config import BlinkConfig
import threading


LED_PIN = 24  # board pin no. 12
TIME_TO_KRAA = None


class Samuel:
    def __init__(self, touch_sensor, audio_queue):
        self.led = LED(LED_PIN)
        self.blinker = self.Blink(led=self.led)
        self.speaker = Speak(blinker=self.blinker)
        self.events = Events()
        self.events.last_interaction_time = time.time()
        self.time_to_look_at_me = 180
        self.audio_lock = threading.Lock()  # lock for audio playback
        self.touch_sensor = touch_sensor
        self.audio_queue = audio_queue
        self.gpio_setup(led=self.led)

    def cleanup(self):
        self.led.off()
        self.led.close()
        self.touch_sensor.bus.close()

    @staticmethod
    def gpio_setup(led):
        led.on()

    class Blink:
        _instance = None
        _initialized = False

        def __init__(self, led):
            if not self._initialized:
                self.lock = threading.Lock()
                self.config = BlinkConfig()
                self.events = Events()
                self._initialized = True
            if led is not None:
                self.led = led

        def __new__(cls, *args, **kwargs):
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
            while not self.events.shutdown_event.is_set():
                # GPIO.output(LED_PIN, GPIO.LOW)
                self.led.off()
                time.sleep(BlinkConfig.BLINK_DURATION)
                self.led.on()

                with self.lock:
                    current_fast = self.config.fast
                    current_slow = self.config.slow

                time_to_wait_between_blinks = random.uniform(current_fast, current_slow)
                if self.events.blink_event.wait(timeout=time_to_wait_between_blinks):
                    self.events.blink_event.clear()

    # def play_audio(self, audio_track, time_to_sleep):
    #     with self.audio_lock:
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)
    #         loop.run_until_complete(
    #             self.speaker.async_speak(audio_track, time_to_sleep)
    #         )

    def head_pat(self):
        last_sound_time = 0.0
        min_interval = 3.0  # seconds before allowing the next pat sound
        while not self.events.shutdown_event.is_set():
            res = self.touch_sensor.poll()
            now = time.time()
            # Only fire on a True transition AND if enough time has passed
            if res is True and (now - last_sound_time) >= min_interval:
                last_sound_time = now
                self.events.head_pat_event.set()  # For use inside animatron_move
                audio_track_to_play = Speak.choose_random_sound_from_category(
                    category=Speak.SoundCategories.HeadPat.name
                )
                self.blinker.change_blinking_time(
                    BlinkConfig.PATTED_FAST, BlinkConfig.PATTED_SLOW
                )
                print("Mmmmmm this feels nice!")
                self.audio_queue.put_nowait(
                    (
                        Speak.SoundCategories.HeadPat.queue_priority,
                        audio_track_to_play,
                        Speak.DEFAULT_GAP,
                    )
                )
                # self.async_speak(audio_track_to_play, time_to_sleep=1040)
                self.events.head_pat_event.clear()
                self.blinker.restore_blinking_time()
                self.events.last_interaction_time = time.time()
            time.sleep(self.touch_sensor.poll_int)

    def look_at_me(self):
        while not self.events.shutdown_event.is_set():
            if (
                time.time() - self.events.last_interaction_time
            ) > self.time_to_look_at_me and not self.events.speaking_event.is_set():
                self.events.look_at_me_event.set()
                self.blinker.change_blinking_time(
                    fast_blink=BlinkConfig.ATTENTION_FAST,
                    slow_blink=BlinkConfig.ATTENTION_SLOW,
                )
                audio_track_to_play = Speak.choose_random_sound_from_category(
                    category=Speak.SoundCategories.LookAtMe.name
                )
                print(f"[DEBUG] Enqueuing audio track: {audio_track_to_play}")
                self.audio_queue.put_nowait(
                    (
                        Speak.SoundCategories.LookAtMe.queue_priority,
                        audio_track_to_play,
                        Speak.DEFAULT_GAP,
                    )
                )
                self.events.last_interaction_time = time.time()
                self.blinker.restore_blinking_time()
                self.events.look_at_me_event.clear()
            time.sleep(0.1)
