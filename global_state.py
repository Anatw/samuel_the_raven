from threading import Event


class Events:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Events, cls).__new__(cls)
            cls._instance.look_at_me_event = Event()
            cls._instance.head_pat_event = Event()
            cls._instance.speaking_event = Event()
            cls._instance.face_detected_event = Event()
            cls._instance.resume_face_tracking_event = Event()
            cls._instance.blink_event = Event()
        return cls._instance

    # Type hints for IDE support
    look_at_me_event: Event
    head_pat_event: Event
    speaking_event: Event
    face_detected_event: Event
    resume_face_tracking_event: Event
    blink_event: Event
