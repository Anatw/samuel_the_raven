# Samuel the Raven

A Python-based animatronic raven integrating speech recognition, face detection & tracking, low-latency audio I/O, capacitive touch sensing, and precise servo-driven movements for lifelike interaction.

---

## Features

- **Offline speech recognition** - Uses Vosk models locally on the Pi - no cloud or internet required  
- **Real-time face detection, recognition & tracking** - Follows faces via the `face-recognition` library  
- **Low-latency audio I/O** - Playback & recording through `sounddevice` for smooth responses  
- **Capacitive touch interaction** - Detects touch through feathers or perches with a custom `smbus2`-based MPR121 driver  
- **Precise servo control** - Pololu Maestro interface drives beak, wings, body, and two-axis head movement (up/down & left/right)  
- **Asynchronous task coordination** - Non-blocking routines let sensing, speaking, and moving run in parallel  

---

## Repository Structure

```text
.
├── Servo.py                          # Maestro servo control interface
├── animatron_move.py                 # Background movement routines
├── animatron_speak.py                # Speech playback and event handling
├── samuel_main.py                    # Entry point for standard operation
├── samuel_async.py                   # Async-driven operation example
├── config.py                         # Behavior and threshold configurations
├── global_state.py                   # Shared events and state definitions
├── timer_window_for_programmer.py    # Developer timing visualization tool
├── touch_sensor.py                   # MPR121 capacitive-touch sensor driver
├── requirements.txt                  # Python dependency list
├── tox.ini                           # Testing & linting configuration
└── README.md                         # Project documentation
```

---

## Hardware Requirements

- **Raspberry Pi** (preferably model 5, with Python 3.8+)  
- **Pololu Maestro** servo controller (USB connection, 6–12 channels)  
- **Standard hobby servos** for beak, two-axis head, wings, and body  
- **USB class-compliant microphone** (any generic USB mic)  
- **Speaker** with 3.5 mm jack or USB audio interface
- **LED indicators** - Two LED lights for the raven's eyes (blinking mechanism)
- **Adafruit MPR121** capacitive-touch breakout for interactive touch sensing 

---

## Software Requirements

- **Python 3.8+**  
- Install dependencies:
  ````bash
  git clone https://github.com/Anatw/samuel_the_raven.git
  cd samuel_the_raven
  pip install -r requirements.txt
  ````
- Key libraries:
  - \`vosk\` for offline speech recognition  
  - \`sounddevice\` & \`PySoundFile\` for audio I/O  
  - \`face-recognition\` for vision-based interaction  
  - \`smbus2\` for I²C communication with MPR121  

---

## Configuration

Edit **config.py** to adjust:
- Movement pulse-width ranges and repetition counts  
- Speech repetition intervals  
- Touch thresholds and debounce settings  
- Face-recognition upsample factor (speed vs. accuracy)  

---

## Usage

  ```bash
  python samuel_main.py
  ```  
  On Raspberry Pi, this also automatically starts the developer timing visualization tool.

---

## Hardware Setup & Calibration

### Audio Setup

1. Connect any USB mic to the Pi’s USB port and verify with:
    ```bash
   arecord -l
    ```
2. In Python, select your mic via \`sounddevice\`:
    ```python
   import sounddevice as sd
   sd.default.device = 'Your USB Mic Name'
    ```

### Touch Sensor Setup

1. Wire VIN → Pi 3.3 V (pin 1); GND → Pi GND (pin 6)  
2. Wire SDA → SDA1 (pin 3, BCM 2); SCL → SCL1 (pin 5, BCM 3)  
3. Enable I²C on the Pi:
    ```bash
   sudo raspi-config
   # Interfacing Options → I2C → enable → reboot
    ```
4. Install \`smbus2\`:
   ```bash
   pip3 install smbus2
   ```
5. Use \`touch_sensor.py\` driver for MPR121 initialization, threshold tuning, debounce, and polling.  
6. Example usage:
   ```python
   from touch_sensor import MPR121TouchSensor

   sensor = MPR121TouchSensor(
       touch_thresh=12,
       release_thresh=6,
       touch_conf=3,
       release_conf=3,
       dt=1,
       dr=1,
       poll_interval=0.1
   )
   ```
7. Troubleshoot I²C with:
   ```bash
   i2cdetect -y 1
   ```

---

## Software Testing & Linting

- We use \`tox\` to manage testing and lint checks  
- Install \`tox\` if needed:
  ````bash
  pip install tox
  ````
- Run all environments:
  ````bash
  tox
  ````
- \`tox.ini\` defines:
  - \`py\` for future pytest suite  
  - \`lint\` for flake8, black, isort, etc.  

---

## Contributing

Contributions are welcome!  
- Open an issue to discuss changes or submit a pull request  
- Ensure code passes:
  ````bash
  tox -e lint
  tox -e py
  ````

---

## Code of Conduct

Please be respectful and inclusive in all project discussions.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

- **Blog** – [Animatronic Menagerie](https://theanimatronicmenagerie.wordpress.com/)  
- **GitHub** – [Anatw](https://github.com/Anatw)

---

*Developed by Anat Wax*
