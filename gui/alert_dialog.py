from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
from utils.alert_manager import AlertManager

class AlertLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alert Log")
        self.resize(500, 400)
        layout = QVBoxLayout(self)

        alerts = AlertManager.instance().get_alerts()
        if not alerts:
            layout.addWidget(QLabel("No alerts yet."))
            return

        table = QTableWidget(len(alerts), 2)
        table.setHorizontalHeaderLabels(["Time", "Alert"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        for row, alert in enumerate(alerts):
            table.setItem(row, 0, QTableWidgetItem(alert["time"]))
            table.setItem(row, 1, QTableWidgetItem(alert["message"]))

        layout.addWidget(table)