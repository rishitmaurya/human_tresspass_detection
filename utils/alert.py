import os
import time
import threading
from playsound import playsound
from utils.logger import log_event
from gui.alert_popup import show_alert_popup
import pygame  # Add this import

# Initialize pygame mixer for better sound control
pygame.mixer.init()

last_alert_time = 0
alert_cooldown = 5  # seconds

def play_alert_sound():
    sound_path = os.path.join("assets", "alert.wav")
    if os.path.exists(sound_path):
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play(-1)  # -1 means loop indefinitely

def stop_alert_sound():
    pygame.mixer.music.stop()

def trigger_alert():
    global last_alert_time
    current_time = time.time()

    if current_time - last_alert_time >= alert_cooldown:
        last_alert_time = current_time

        log_event("Intrusion Detected")

        # Play sound in a non-blocking way
        threading.Thread(target=play_alert_sound, daemon=True).start()

        # Show GUI popup and stop sound when closed
        show_alert_popup("ALERT!", "Human entered restricted area!")
        stop_alert_sound()