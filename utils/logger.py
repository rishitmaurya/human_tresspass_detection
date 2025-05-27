# logger.py
import os
from datetime import datetime

LOG_FILE = os.path.join("logs", "alert_log.txt")

def log_event(event):
    """
    Appends an event to the alert log with a timestamp.

    Args:
        event (str): Description of the event
    """
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {event}\n"

    with open(LOG_FILE, "a") as f:
        f.write(entry)
