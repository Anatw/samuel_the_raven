import time
import errno
import smbus2


class MPR121TouchSensor:
    def __init__(
        self,
        touch_thresh: int,  # Threshold above baseline
        release_thresh: int,  # Threshold below baseline
        touch_conf: int,  # Software-debounce touch confirms
        release_conf: int,  # Software-debounce release confirms
        dt: int,  # Hardware debounce DT
        dr: int,  # Hardware debounce DR
        poll_interval: float,  # Number of seconds between polls
        i2c_bus: int = 1,
        address: int = 0x5A,
        electrode: int = 11,
    ):
        self.addr = address
        self.electrode = electrode
        self.touch_thresh = touch_thresh
        self.release_thresh = release_thresh
        self.dt = dt
        self.dr = dr
        self.touch_conf = touch_conf
        self.release_conf = release_conf
        self.poll_int = poll_interval

        # Registers
        self.R_SOFTRESET = 0x80
        self.R_ELE_CFG = 0x5E
        self.R_DEBOUNCE = 0x5B
        self.R_TOUCH_BASE = 0x41 + 2 * electrode
        self.R_RELEASE_BASE = 0x42 + 2 * electrode
        self.R_STATUS_L = 0x00

        self._i2c_bus = i2c_bus
        self.bus = smbus2.SMBus(self._i2c_bus)
        self._reset_counts()
        for attempt in range(3):
            try:
                self._init_sensor()
                break
            except OSError as e:
                if e.errno != 121 or attempt == 2:
                    raise
                time.sleep(0.05)

    def _init_sensor(self):
        self.bus.write_byte_data(self.addr, self.R_SOFTRESET, 0x63)  # Soft-reset
        time.sleep(0.1)
        self.bus.write_byte_data(self.addr, self.R_ELE_CFG, 0x00)  # Stop electrodes
        self.bus.write_byte_data(self.addr, self.R_TOUCH_BASE, self.touch_thresh)
        self.bus.write_byte_data(self.addr, self.R_RELEASE_BASE, self.release_thresh)
        self.bus.write_byte_data(self.addr, self.R_DEBOUNCE, (self.dr << 4) | self.dt)
        self.bus.write_byte_data(
            self.addr, self.R_ELE_CFG, 0x8F
        )  # Re-enable electrodes
        self._reset_counts()

    def _reset_counts(self):
        self._touch_count = 0
        self._release_count = 0
        self.in_touch = False

    def read_raw_status(self):
        data = self.bus.read_i2c_block_data(self.addr, self.R_STATUS_L, 2)
        mask = data[0] | (data[1] << 8)
        return bool(mask & (1 << self.electrode))

    def poll(self):
        """
        Call regularly; returns True on confirmed touch transition, False on release."""
        try:
            is_touch = self.read_raw_status()
        except (OSError, TypeError) as e:
            # Only recover on the known Remote I/O or closed‐fd errors
            code = getattr(e, "errno", None)
            if isinstance(e, TypeError) or code in (errno.EREMOTEIO, 121):
                # Attempt a graceful re-init, but don’t explode if it still fails
                try:
                    self.bus.close()
                except OSError or TypeError:
                    pass
                time.sleep(0.2)
                # Reopen bus
                self.bus = smbus2.SMBus(self._i2c_bus)
                # Try init up to 3 times
                for _ in range(3):
                    try:
                        self._init_sensor()
                        break
                    except OSError:
                        time.sleep(0.1)
                else:
                    print(
                        "Inside touch_sensor - poll - re-init failed 3 times, skipping until next poll"
                    )
                return None
            # If it was some other error, bubble it up
            raise

        # Software debounce
        if is_touch:
            self._touch_count += 1
            self._release_count = 0
        else:
            self._release_count += 1
            self._touch_count = 0

        # Transitions
        if not self.in_touch and self._touch_count >= self.touch_conf:
            self.in_touch = True
            return True
        if self.in_touch and self._release_count >= self.release_conf:
            self.in_touch = False
            return False
        return None
