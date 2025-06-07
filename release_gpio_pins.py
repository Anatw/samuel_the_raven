# filepath: release_gpio.py
from gpiozero import LED

for pin in range(2, 28):
    try:
        led = LED(pin)
        led.close()
        print(f"Released pin {pin}")
    except Exception as e:
        print(f"Could not release pin {pin}: {e}")
        pass
    