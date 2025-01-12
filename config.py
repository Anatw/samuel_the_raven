class BlinkConfig:
    DEFAULT_FAST = 4
    DEFAULT_SLOW = 23
    PATTED_FAST = 0.3
    PATTED_SLOW = 2.6
    ATTENTION_FAST = 0.7
    ATTENTION_SLOW = 3.2
    SPEAKING_FAST = 0.5
    SPEAKING_SLOW = 3
    BLINK_DURATION = 0.115

    def __init__(self):
        self.fast = self.DEFAULT_FAST
        self.slow = self.DEFAULT_SLOW

    def set_blink_rate(self, fast, slow):
        self.fast = fast
        self.slow = slow
