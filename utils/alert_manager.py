import threading
from datetime import datetime

class AlertManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.alerts = []

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = AlertManager()
            return cls._instance

    def add_alert(self, message):
        now = datetime.now()
        self.alerts.append({
            "time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "message": message
        })

    def get_alerts(self):
        return list(self.alerts)