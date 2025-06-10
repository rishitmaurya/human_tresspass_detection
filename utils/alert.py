from PyQt5.QtMultimedia import QSound
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QApplication

alert_sound = None
alert_timer = None

def show_alert_popup():
    parent = QApplication.activeWindow()
    QMessageBox.warning(parent, "Intrusion Detected", "INTRUDER detected in ROI!")

def trigger_alert():
    global alert_sound, alert_timer
    if alert_sound is None:
        alert_sound = QSound("assets\\alert.wav")  # Use your alert sound file path

    if not alert_sound.isFinished():  # Already playing
        return

    alert_sound.play()

    # Show alert pop-up (on main thread)
    QTimer.singleShot(0, show_alert_popup)

    # Stop after 5 seconds
    if alert_timer is not None:
        alert_timer.stop()
    alert_timer = QTimer()
    alert_timer.setSingleShot(True)
    alert_timer.timeout.connect(stop_alert)
    alert_timer.start(5000)  # 5000 ms = 5 seconds

def stop_alert():
    global alert_sound
    if alert_sound:
        alert_sound.stop()