from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHeaderView,
    QLineEdit, QHBoxLayout, QSizePolicy, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from utils.alert_manager import AlertManager

class AlertLogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alert Log")
        self.resize(600, 450)
        self.setMinimumSize(400, 300)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        header_label = QLabel("Alert Log")
        header_font = QFont("Segoe UI", 16, QFont.Bold)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)

        # Search bar layout
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setFont(QFont("Segoe UI", 10))
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter alerts...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_alerts)
        search_layout.addWidget(self.search_input)

        main_layout.addLayout(search_layout)

        self.alerts = AlertManager.instance().get_alerts()
        if not self.alerts:
            no_alert_label = QLabel("No alerts yet.")
            no_alert_label.setAlignment(Qt.AlignCenter)
            no_alert_label.setFont(QFont("Segoe UI", 12, QFont.StyleItalic))
            no_alert_label.setStyleSheet("color: #666666;")
            main_layout.addWidget(no_alert_label)
            return

        self.table = QTableWidget(len(self.alerts), 2)
        self.table.setHorizontalHeaderLabels(["Time", "Alert"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                font-family: 'Segoe UI';
                font-size: 11pt;
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                gridline-color: #dddddd;
            }
            QHeaderView::section {
                background-color: #3f51b5;
                color: white;
                padding: 4px;
                font-weight: 600;
                font-size: 11pt;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #c5cae9;
                color: #1a237e;
            }
        """)

        for row, alert in enumerate(self.alerts):
            time_item = QTableWidgetItem(alert["time"])
            message_item = QTableWidgetItem(alert["message"])
            self.table.setItem(row, 0, time_item)
            self.table.setItem(row, 1, message_item)

        self.table.resizeRowsToContents()
        main_layout.addWidget(self.table)

    def filter_alerts(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            time_item = self.table.item(row, 0)
            message_item = self.table.item(row, 1)
            row_text = (time_item.text() + " " + message_item.text()).lower()
            self.table.setRowHidden(row, text not in row_text)