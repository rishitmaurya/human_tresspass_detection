# alert_popup.py
from PyQt5.QtWidgets import QMessageBox

def show_alert_popup(title, message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()
