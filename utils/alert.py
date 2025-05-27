# alert.py
import os
import time
import threading
from playsound import playsound
from utils.logger import log_event
from gui.alert_popup import show_alert_popup

last_alert_time = 0
alert_cooldown = 5  # seconds

def play_alert_sound():
    sound_path = os.path.join("assets", "alert.mp3")
    if os.path.exists(sound_path):
        playsound(sound_path)

def trigger_alert():
    global last_alert_time
    current_time = time.time()

    if current_time - last_alert_time >= alert_cooldown:
        last_alert_time = current_time

        log_event("Intrusion Detected")

        # Play sound in a non-blocking thread
        threading.Thread(target=play_alert_sound, daemon=True).start()

        # Show GUI popup (blocking in main thread)
        show_alert_popup("ALERT!", "Human entered restricted area!")
