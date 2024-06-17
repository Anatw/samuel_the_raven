import maestro
import random
from time import sleep

maestro_controller = maestro.Controller(ttyStr='/dev/ttyACM0')


class Servo:
	def __init__(
		self,
		max_value=None,
		min_value=None,
		pin_number=None,
		gesticulation_repetition=None
	):
		# pin_number (int): servo number on the Pololu Maestro controller
		self.max_value = max_value
		self.min_value = min_value
		self.pin_number = pin_number
		self.gesticulation_repetition = gesticulation_repetition

		self.mid_value = int((min_value + max_value) / 2)
	
	def get_position(self):
		return maestro_controller.getPosition(self.pin_number)
		
	def set_position(self, target_value):
		maestro_controller.setTarget(self.pin_number,target_value)
		return
	
	def generate_random_value(self, destiny):
		# destiny is the requested value for servo, in int.
		current_position = self.get_position()
		if current_position == destiny:
			return current_position
		# Make sure that the higer number is the current_position
		if current_position < destiny:
			return random.randint(current_position, destiny)
		return random.randint(destiny, current_position)
	
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
		return random_float ** 2 * 3
	
	def gesticulation(self):
		for index in range(1,self.gesticulation_repetition):
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
		self.move_max(target_value)
	
	def move_down(self, target_value=None):
		self.move_min(target_value)


class Body(Servo):
	# The lower the value is, the higher the body will reach ->
	# max_value => body down, min_value => body up
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
