import random
import time
import asyncio
import threading

from Servo import Movement
from utils import get_random_weighted_sleep_time

TIME_TO_TRACK_FACE = 23


class Move:
    def __init__(self, events):
        self.events = events
        self.body_flap_thread = None

    movements = {
        11: "Movement.head_rl.move_right()",
        12: "Movement.head_rl.move_left()",
        21: "Movement.head_ud.move_up()",
        22: "Movement.head_ud.move_down()",
        31: "Movement.body.move_up()",
        32: "Movement.body.move_down()",
        41: "Movement.wings.move_up()",
        42: "Movement.wings.move_down()",
        51: "Movement.mouth.open()",
        52: "Movement.mouth.close()",
    }
    movements_keys = list(movements.keys())
    sleep_uniform = (0.5, 2.2)  # (0.5,1.2)

    # gesticulation
    async def move_wings():
        Movement.wings.move_up()
        await asyncio.sleep(random.uniform(*Move.sleep_uniform))
        Movement.wings.move_down()

    async def move_head_rl():
        Movement.head_rl.move_right()
        await asyncio.sleep(random.uniform(*Move.sleep_uniform))
        Movement.head_rl.move_left()

    async def move_head_ud():
        Movement.head_ud.move_down()
        await asyncio.sleep(random.uniform(*Move.sleep_uniform))
        Movement.head_ud.move_up()

    async def move_body():
        Movement.body.move_up()
        await asyncio.sleep(random.uniform(*Move.sleep_uniform))
        Movement.body.move_down()

    async def async_move():
        await asyncio.gather(
            Move.move_wings(),
            Move.move_head_rl(),
            Move.move_head_ud(),
            Move.move_body(),
        )

    def get_random_duo_combination(self):
        first_number = random.choice(self.movements_keys)
        first_digit = first_number // 10
        # Create a list of numbers that do not start with the first digit
        remaining_numbers = [
            number for number in self.movements_keys if number // 10 != first_digit
        ]
        second_number = random.choice(remaining_numbers)
        return self.movements[first_number], self.movements[second_number]

    async def random_async_move(self):
        random_duo_combination = self.get_random_duo_combination()
        exec(random_duo_combination[0])
        exec(random_duo_combination[1])

    def move_body_flap_wings_face_detection(self):
        """
        Non-blocking face-tracking flaps: schedule the end of the window
        immediately, then do repeated flaps in small sleeps.
        """

        def _abortable_sleep(duration: float):
            end = time.time() + duration
            while time.time() < end:
                if (
                    not self.events.face_detected_event.is_set()
                    or self.events.shutdown_event.is_set()
                ):
                    return
                time.sleep(0.05)

        # 1) Schedule clearing the face flag after the TRACK window
        t = threading.Timer(TIME_TO_TRACK_FACE, self.events.face_detected_event.clear)
        t.daemon = True
        t.start()

        while (
            self.events.face_detected_event.is_set()
            and not self.events.shutdown_event.is_set()
        ):
            asyncio.run(Move.move_body())
            _abortable_sleep(random.uniform(0.6, 4.8))
            asyncio.run(Move.move_wings())
            _abortable_sleep(random.uniform(0.6, 3.4))

    # async def move_body_face_detection(self):
    #     while self.events.face_detected_event.is_set():
    #         Movement.body.set_position(
    #             Movement.body.get_position() - random.randint(25, 60)
    #         )
    #         await time.sleep(random.uniform(0.6, 6.4))
    #         Movement.body.set_position(
    #             Movement.body.get_position() + random.randint(25, 60)
    #         )

    def resume_tracking_faces(self):
        self.events.resume_face_tracking_event.set()
        self.events.head_pat_event.clear()
        self.events.look_at_me_event.clear()

    def move(self):
        # This process allow Samuel to move while doing other routines such as speaking. The movement is always available in the background.
        self.events.resume_face_tracking_event.set()
        should_start_movement_cycle = True
        idle_resume_timer = None
        self.body_flap_thread = None

        while not self.events.shutdown_event.is_set():
            if should_start_movement_cycle:
                starting_time = time.time()
                random_time_to_sleep = get_random_weighted_sleep_time()
                should_start_movement_cycle = False

            if self.events.look_at_me_event.is_set():
                asyncio.run(Move.async_move())

            if self.events.head_pat_event.is_set():
                Movement.body.move_down()
                Movement.head_ud.move_up()
                time.sleep(random.uniform(0.5, 1.2))
                Movement.head_rl.move_right()
                Movement.body.move_up(Movement.body.mid_value)
                Movement.head_ud.move_down()
                Movement.head_rl.move_left()

            if self.events.face_detected_event.is_set() and (
                self.body_flap_thread is None or not self.body_flap_thread.is_alive()
            ):
                # Follow the face for some time, than it will get boared and stop following it and get back to moving randomly.
                self.body_flap_thread = threading.Thread(
                    target=self.move_body_flap_wings_face_detection, daemon=True
                )
                self.body_flap_thread.start()
                print("boooooooooo")

            if (
                not self.events.head_pat_event.is_set()
                and not self.events.look_at_me_event.is_set()
                and not self.events.face_detected_event.is_set()
                and time.time() >= (starting_time + random_time_to_sleep)
            ):
                threading.Thread(
                    target=lambda: asyncio.run(self.random_async_move()), daemon=True
                ).start()

                # Cancel any pending timer so we don’t stack them
                if idle_resume_timer and idle_resume_timer.is_alive():
                    idle_resume_timer.cancel()

                # Immediately re-allow face detection (unblock camera guard)
                self.events.resume_face_tracking_event.set()

                # Then *schedule* a pause on *re*-detecting for TIME_TO_TRACK_FACE
                idle_resume_timer = threading.Timer(
                    TIME_TO_TRACK_FACE, self.events.resume_face_tracking_event.clear
                )
                idle_resume_timer.daemon = True
                idle_resume_timer.start()

                # prep for next idle window
                should_start_movement_cycle = True

        # small throttle so we don't max out CPU
        time.sleep(0.05)
