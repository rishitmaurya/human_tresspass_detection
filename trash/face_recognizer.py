import os
from datetime import datetime
import cv2
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from queue import Queue
from threading import Lock

LOG_FILE = os.path.join("logs", "alert_log.html")
IMAGES_DIR = os.path.join("logs", "images")
event_counter = 0
log_lock = Lock()

class LogWorker(QThread):
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.queue = Queue()
        self.running = True
        
    def process_log(self, event, frame, person_name):
        self.queue.put((event, frame.copy() if frame is not None else None, person_name))
        
    def run(self):
        while self.running:
            try:
                event, frame, person_name = self.queue.get(timeout=0.1)
                _write_log_entry(event, frame, person_name)
                self.queue.task_done()
            except Queue.Empty:
                continue
            except Exception as e:
                print(f"Error in log worker: {str(e)}")
                continue
                
    def stop(self):
        self.running = False

def _write_log_entry(event, frame=None, person_name=None):
    """Internal function to write the log entry"""
    global event_counter
    
    with log_lock:
        event_counter += 1
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)

        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M:%S")

        # Save image if provided
        image_path = None
        if frame is not None:
            image_filename = f"intrusion_{event_counter}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            image_path = os.path.join(IMAGES_DIR, image_filename)
            cv2.imwrite(image_path, frame)

        # Keep your existing HTML template and file handling code here
        # ... (keep all the HTML and file handling code from the original logger.py)

# Create global logger instance
log_worker = LogWorker()
log_worker.start()

def log_event(event, frame=None, person_name=None):
    """Thread-safe function to log events"""
    log_worker.process_log(event, frame, person_name)

# Cleanup function to be called when the application exits
def cleanup():
    log_worker.stop()
    log_worker.wait()