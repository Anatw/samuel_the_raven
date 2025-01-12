import random
import time
import multiprocessing
import asyncio
import threading

from Servo import Movement
from utils import get_random_weighted_sleep_time
from global_state import Events

TIME_TO_TRACK_FACE = 23


class Move:
    def __init__(self):
        self.events = Events()

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
        print("move_wings")
        Movement.wings.move_up()
        await asyncio.sleep(random.uniform(*Move.sleep_uniform))
        Movement.wings.move_down()

    async def move_head_rl():
        print("move_head_rl")
        Movement.head_rl.move_right()
        await asyncio.sleep(random.uniform(*Move.sleep_uniform))
        Movement.head_rl.move_left()

    async def move_head_ud():
        print("move_head_ud")
        Movement.head_ud.move_down()
        await asyncio.sleep(random.uniform(*Move.sleep_uniform))
        Movement.head_ud.move_up()

    async def move_body():
        print("move_body")
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

    def get_random_duo_combination():
        first_number = random.choice(Move.movements_keys)
        first_digit = first_number // 10
        # Create a list of numbers that do not start with the first digit
        remaining_numbers = [
            number for number in Move.movements_keys if number // 10 != first_digit
        ]
        second_number = random.choice(remaining_numbers)
        return Move.movements[first_number], Move.movements[second_number]

    async def random_async_move():
        random_duo_combination = Move.get_random_duo_combination()
        exec(random_duo_combination[0])
        exec(random_duo_combination[1])

    def flap_wings_face_detection(self):
        while self.events.face_detected_event.is_set():
            asyncio.run(Move.move_body())
            time.sleep(random.uniform(0.6, 4.8))
            asyncio.run(Move.move_wings())
            time.sleep(random.uniform(0.6, 3.4))

    async def move_body_face_detection(self):
        while self.events.face_detected_event.is_set():
            Movement.body.set_position(
                Movement.body.get_position() - random.randint(25, 60)
            )
            await time.sleep(random.uniform(0.6, 6.4))
            Movement.body.set_position(
                Movement.body.get_position() + random.randint(25, 60)
            )

    def resume_tracking_faces(self):
        self.events.resume_face_tracking_event.set()

    def move(self):
        # This process allow Samuel to move while doing other routines such as speaking. The movement is always available in the background.
        should_start_movement_cycle = True
        while True:
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
            if self.events.face_detected_event.is_set():
                # Follow the face for some time, than it will get borring and stop following it and get back to moving randomly.
                # Flap wings every some time:
                Move.flap_wings_face_detection()
                time.sleep(TIME_TO_TRACK_FACE)
                print("boooooooooo")
                self.events.face_detected_event.clear()
                # Take some break from tracking faces and move randomly:
                timer = threading.Timer(
                    interval=8.0, function=Move.resume_tracking_faces
                )
                timer.start()
            if not (
                self.events.head_pat_event.is_set()
                or self.events.look_at_me_event.is_set()
            ) and time.time() >= (starting_time + random_time_to_sleep):
                process2 = multiprocessing.Process(
                    target=asyncio.run(Move.random_async_move())
                )
                process2.start()
                process2.join()
                should_start_movement_cycle = True
