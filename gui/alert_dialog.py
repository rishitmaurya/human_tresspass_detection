from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
import os
from bs4 import BeautifulSoup

class AlertLogDialog(QDialog):
    def __init__(self, parent=None, log_file="logs/alert_log.html"):
        super().__init__(parent)
        self.setWindowTitle("Alert Log")
        self.resize(800, 500)
        layout = QVBoxLayout(self)

        if not os.path.exists(log_file):
            layout.addWidget(QLabel("No alerts logged yet."))
            return

        # Parse the HTML log file
        with open(log_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            table = soup.find("table")
            if not table:
                layout.addWidget(QLabel("No alerts found in log."))
                return

            rows = table.find_all("tr")
            if not rows or len(rows) < 2:
                layout.addWidget(QLabel("No alerts found in log."))
                return

            headers = [th.text.strip() for th in rows[0].find_all("th")]
            data_rows = rows[1:]

            table_widget = QTableWidget(len(data_rows), len(headers))
            table_widget.setHorizontalHeaderLabels(headers)
            table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table_widget.verticalHeader().setVisible(False)
            table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

            for row_idx, row in enumerate(data_rows):
                cols = row.find_all("td")
                for col_idx, col in enumerate(cols):
                    # For the Evidence column, show text or image filename
                    if headers[col_idx].lower() == "evidence":
                        img = col.find("img")
                        value = os.path.basename(img["src"]) if img and img.has_attr("src") else col.text.strip()
                    else:
                        value = col.text.strip()
                    table_widget.setItem(row_idx, col_idx, QTableWidgetItem(value))

            layout.addWidget(table_widget)