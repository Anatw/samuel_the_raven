import maestro
import random
from time import sleep
from threading import Lock


HEAD_SHOULD_LIFT = False
HEAD_SHOULD_TURN_LEFT = False
HEAD_SHOULD_TURN_RIGHT = False
BODY_MIN_VALUE = 5000
BODY_MAX_VALUE = 6200
BODY_RANGE = BODY_MAX_VALUE - BODY_MIN_VALUE


class SerialManager:
    _instance = None
    _lock = Lock()

    def __new__(cls, ttyStr="/dev/ttyACM0"):
        if cls._instance is None:
            cls._instance = super(SerialManager, cls).__new__(cls)
            cls._instance.controller = maestro.Controller(ttyStr=ttyStr)
        return cls._instance

    def get_position(self, pin_number):
        with self._lock:
            return self.controller.getPosition(pin_number)

    def set_position(self, pin_number, target_value):
        with self._lock:
            self.controller.setTarget(pin_number, target_value)

    def set_speed(self, pin_number, speed):
        with self._lock:
            self.controller.setSpeed(chan=pin_number, speed=speed)


# Global instance of SerialManager
serial_manager = SerialManager()


class Servo:
    def __init__(
        self,
        max_value=None,
        min_value=None,
        pin_number=None,
        gesticulation_repetition=None,
    ):
        self.max_value = max_value
        self.min_value = min_value
        self.pin_number = pin_number  # servo number on the Pololu Maestro controller
        self.gesticulation_repetition = gesticulation_repetition

        self.mid_value = int((min_value + max_value) / 2)

    def get_position(self):
        # print(f"In get_position, Sending command: {command}")
        # print(f"In get_position, Received data: {data}")
        return serial_manager.get_position(self.pin_number)

    def set_position(self, target_value):
        # print(f"In set_position, Sending command: {command}")
        # print(f"In set_position, Received data: {data}")
        serial_manager.set_position(self.pin_number, target_value)

    def generate_random_value(self, destiny):
        # Destiny is the requested value for servo, in int.
        current_position = self.get_position()
        if current_position == destiny:
            return current_position
        # Make sure that the higer number is the current_position
        return random.randint(
            min(current_position, destiny), max(current_position, destiny)
        )

    def move_max(self, target_value=None):
        if not target_value:
            target_value = self.generate_random_value(destiny=self.max_value)
        self.set_position(target_value=target_value)

    def move_min(self, target_value=None):
        if not target_value:
            target_value = self.generate_random_value(destiny=self.min_value)
        self.set_position(target_value=target_value)

    def random_sleep_value():
        random_float = random.random()
        return random_float**2 * 3

    def gesticulation(self):
        for index in range(1, self.gesticulation_repetition):
            self.move_max()
            sleep(Servo.random_sleep_value())
            self.move_min()
            sleep(Servo.random_sleep_value())


class Mouth(Servo):
    def __init__(
        self,
        max_value,
        min_value,
        pin_number,
        gesticulation_repetition,
    ):
        super().__init__(
            max_value,
            min_value,
            pin_number,
            gesticulation_repetition,
        )

    def open(self, target_value=None):
        self.move_max(target_value)

    def close(self, target_value=None):
        self.move_min(target_value)


class HeadUpDown(Servo):
    def __init__(
        self,
        max_value,
        min_value,
        pin_number,
        gesticulation_repetition,
    ):
        super().__init__(
            max_value,
            min_value,
            pin_number,
            gesticulation_repetition,
        )

    def move_up(self, target_value=None):
        self.move_max(target_value)

    def move_down(self, target_value=None):
        self.move_min(target_value)


class HeadLeftRight(Servo):
    # lower numbers will turn left, higher numbers will turn right ->
    # min_value => left, max_value => right
    def __init__(
        self,
        max_value,
        min_value,
        pin_number,
        gesticulation_repetition,
    ):
        super().__init__(
            max_value,
            min_value,
            pin_number,
            gesticulation_repetition,
        )

    def move_left(self, target_value=None):
        self.move_min(target_value)

    def move_right(self, target_value=None):
        self.move_max(target_value)


# class Head(HeadLeftRight, HeadUpDown):
#     # self = HeadUpDown
#     def __init__(self, head_rl, head_ud):
#         super(HeadLeftRight, self).__init__(
#             max_value=head_rl.max_value,
#             min_value=head_rl.min_value,
#             pin_number=head_rl.pin_number,
#             gesticulation_repetition=head_rl.gesticulation_repetition,
#         )
#         # Initialize HeadUpDown with values from head_ud
#         super(HeadUpDown, self).__init__(
#             max_value=head_ud.max_value,
#             min_value=head_ud.min_value,
#             pin_number=head_ud.pin_number,
#             gesticulation_repetition=head_ud.gesticulation_repetition,
#         )

#     def move_right(self, head_lr_instance, target_value=None):
#         global HEAD_SHOULD_LIFT, HEAD_SHOULD_TURN_RIGHT
#         HEAD_SHOULD_TURN_RIGHT = False
#         if not target_value:
#             # target_value = head_lr_instance.generate_random_value
#             # (destiny=head_lr_instance.max_value)
#             target_value = head_lr_instance.max_value
#         import ipdb

#         ipdb.set_trace()
#         if target_value > head_lr_instance.mid_value and HEAD_SHOULD_LIFT:
#             # Need to also move head up to compensate:
#             import ipdb

#             ipdb.set_trace()
#             HEAD_SHOULD_LIFT = False
#             head_ud_current_position = self.get_position()
#             self.move_max(
#                 int(head_ud_current_position + (head_ud_current_position * 0.3))
#             )
#         head_lr_instance.move_max(target_value)

#     def move_left(self, head_lr_instance, target_value=None):
#         # head_lr_instance.move_min(target_value)
#         global HEAD_SHOULD_TURN_LEFT
#         HEAD_SHOULD_TURN_LEFT = True
#         if not target_value:
#         head_lr_instance.move_min(head_lr_instance.min_value)

#     def move_up(self, head_lr_instance, target_value=None):
#         import ipdb

#         ipdb.set_trace()
#         global HEAD_SHOULD_LIFT, HEAD_SHOULD_TURN_RIGHT
#         HEAD_SHOULD_LIFT = True
#         if not target_value:
#             # target_value = self.generate_random_value(destiny=self.max_value)
#             target_value = self.max_value
#         if target_value < self.mid_value and HEAD_SHOULD_TURN_RIGHT:
#             # Need to also move head right (min_value) to compensate:
#             HEAD_SHOULD_TURN_RIGHT = False
#             head_rl_current_position = head_lr_instance.get_position()
#             head_lr_instance.set_position(
#                 int(head_rl_current_position - (head_rl_current_position * 0.4))
#             )
#         self.move_max(target_value)

#     def move_down(self, head_lr_instance, target_value=None):
#         # self.move_min(target_value)
#         # self.move_min(self.min_value)
#         #
#         global HEAD_SHOULD_LIFT, HEAD_SHOULD_TURN_LEFT
#         HEAD_SHOULD_LIFT = True
#         if not target_value:
#             # target_value = self.generate_random_value(destiny=self.max_value)
#             target_value = self.min_value
#         if target_value > self.mid_value and HEAD_SHOULD_TURN_LEFT:
#             import ipdb

#             ipdb.set_trace()
#             # Need to also move head left (max_value) to compensate:
#             HEAD_SHOULD_TURN_LEFT = False
#             head_rl_current_position = head_lr_instance.get_position()
#             head_lr_instance.set_position(
#                 int(head_rl_current_position + (head_rl_current_position * 0.4))
#             )
#         self.move_min(target_value)


class Wings(Servo):
    # The lower the number the higher the wings will reach ->
    # max_value => wings down, min_value => wings up
    def __init__(
        self,
        max_value,
        min_value,
        pin_number,
        gesticulation_repetition,
    ):
        super().__init__(
            max_value,
            min_value,
            pin_number,
            gesticulation_repetition,
        )

    def move_up(self, target_value=None):
        self.move_min(target_value)

    def move_down(self, target_value=None):
        self.move_max(target_value)


class Body(Servo):
    # The lower the value is, the higher the body will reach ->
    # max_value => body down, min_value => body up
    def __init__(
        self,
        max_value,
        min_value,
        pin_number,
        range,
        gesticulation_repetition,
    ):
        super().__init__(
            max_value,
            min_value,
            pin_number,
            gesticulation_repetition,
        )
        self.range = range

    def move_up(self, target_value=None):
        self.move_min(target_value)

    def move_down(self, target_value=None):
        self.move_max(target_value)

    def move_min(self, target_value=None):
        if not target_value:
            target_value = self.generate_random_value(destiny=self.min_value)

        current_position = self.get_position()
        new_position_ratio = target_value - current_position
        if new_position_ratio <= (self.range / 10):
            serial_manager.set_speed(
                pin_number=Movement.body.pin_number, speed=4
            )  # Small lmove - move slow
        elif new_position_ratio >= (self.range / 2):
            serial_manager.set_speed(
                pin_number=Movement.body.pin_number, speed=50
            )  # Big move - move very fast
        else:
            serial_manager.set_speed(
                pin_number=Movement.body.pin_number, speed=30
            )  # Medium move - move fast
        self.set_position(target_value=target_value)

    def move_max(self, target_value=None):
        if not target_value:
            target_value = self.generate_random_value(destiny=self.max_value)

        current_position = self.get_position()
        new_position_ratio = current_position - target_value
        if new_position_ratio <= (self.range / 10):
            serial_manager.set_speed(
                pin_number=Movement.body.pin_number, speed=4
            )  # Small lmove - move slow
        elif new_position_ratio >= (self.range / 2):
            serial_manager.set_speed(
                pin_number=Movement.body.pin_number, speed=50
            )  # Big move - move very fast
        else:
            serial_manager.set_speed(
                pin_number=Movement.body.pin_number, speed=30
            )  # Nedium move - move fast
        self.set_position(target_value=target_value)


class Movement:
    mouth = Mouth(
        pin_number=0, min_value=6200, max_value=9200, gesticulation_repetition=1  # 9250
    )
    # For head up-down movement, lower numbers will turn down, higher numbers will turn up:
    head_ud = HeadUpDown(
        pin_number=1, min_value=4450, max_value=8400, gesticulation_repetition=4
    )
    head_rl = HeadLeftRight(
        pin_number=2, min_value=3300, max_value=7100, gesticulation_repetition=5
    )
    # head = Head(head_rl, head_ud)
    wings = Wings(
        pin_number=3, min_value=4600, max_value=5850, gesticulation_repetition=3
    )
    body = Body(
        pin_number=4,
        min_value=BODY_MIN_VALUE,
        max_value=BODY_MAX_VALUE,
        range=BODY_RANGE,
        gesticulation_repetition=2,
    )
