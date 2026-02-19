from threading import Event
import time


class Events:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Events, cls).__new__(cls)
            cls._instance.look_at_me_event = Event()
            cls._instance.head_pat_event = Event()
            cls._instance.speaking_event = Event()
            cls._instance.face_detected_event = Event()
            cls._instance.face_tracking_activate_event = Event()
            cls._instance.blink_event = Event()
            cls._instance.shutdown_event = Event()

            cls._instance.last_interaction_time = time.time()

        return cls._instance

    # Type hints for IDE support
    look_at_me_event: Event
    head_pat_event: Event
    speaking_event: Event
    face_detected_event: Event
    face_tracking_activate_event: Event
    blink_event: Event
    shutdown_event: Event

    last_interaction_time: float
