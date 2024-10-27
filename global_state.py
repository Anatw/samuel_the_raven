import multiprocessing


class Events():
	look_at_me_event = multiprocessing.Event()
	head_pat_event = multiprocessing.Event()
	speaking_event = multiprocessing.Event()
	face_detected_event = multiprocessing.Event()
	resume_face_tracking_event = multiprocessing.Event()
