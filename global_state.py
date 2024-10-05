import multiprocessing


class Events():
	look_at_me_event = multiprocessing.Event()
	head_pat_event = multiprocessing.Event()
	speaking_event = multiprocessing.Event()
