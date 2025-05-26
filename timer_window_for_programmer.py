import tkinter as tk


class TimerWindow:
    def __init__(self):
        self.duration = 0
        self.root = tk.Tk()
        self.root.title("Timer Window")
        self.label = tk.Label(self.root, text="", font=("Helvetica", 48))
        self.label.pack(pady=20)
        self.update_timer()

    def update_timer(self):
        minutes, seconds = divmod(self.duration, 60)
        time_format = f"{minutes:02}:{seconds:02}"
        self.label.config(text=time_format)
        self.duration += 1
        self.root.after(1000, self.update_timer)

    def start(self):
        self.root.mainloop()


def show_timer_window():
    print("[debug] Timer window launched!")
    timer_window = TimerWindow()
    timer_window.start()
