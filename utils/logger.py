import os
from datetime import datetime
import cv2
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from queue import Queue, Empty
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
            except Empty:
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

        # Create or update HTML log
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding='utf-8') as f:
                f.write("""
                <html>
                <head>
                    <style>
                        * { 
                            margin: 0;
                            padding: 0;
                            box-sizing: border-box;
                        }
                        body { 
                            font-family: 'Segoe UI', system-ui, sans-serif;
                            background: #f0f2f5;
                            padding: 2rem;
                        }
                        .container {
                            max-width: 1200px;
                            margin: 0 auto;
                            background: white;
                            border-radius: 12px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                            overflow: hidden;
                        }
                        .header {
                            background: #1a237e;
                            color: white;
                            padding: 1.5rem 2rem;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                        }
                        .header h2 {
                            font-size: 1.5rem;
                            font-weight: 500;
                        }
                        .total-count {
                            background: rgba(255,255,255,0.2);
                            padding: 0.5rem 1rem;
                            border-radius: 6px;
                            font-size: 0.9rem;
                        }
                        table { 
                            width: 100%;
                            border-collapse: collapse;
                        }
                        th { 
                            background: #f8f9fa;
                            color: #1a237e;
                            font-weight: 600;
                            font-size: 0.85rem;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                            padding: 1rem;
                            border-bottom: 2px solid #e0e0e0;
                        }
                        td { 
                            padding: 1rem;
                            border-bottom: 1px solid #eee;
                            color: #333;
                            font-size: 0.95rem;
                        }
                        tr:hover {
                            background: #fafafa;
                        }
                        .serial {
                            font-weight: 600;
                            color: #1a237e;
                            width: 80px;
                        }
                        .timestamp {
                            color: #666;
                            width: 120px;
                        }
                        .event-text {
                            color: #d32f2f;
                            font-weight: 500;
                        }
                        .person-name {
                            color: #1976d2;
                            font-weight: 500;
                            width: 150px;
                        }
                        .unknown {
                            color: #ff9800;
                            font-style: italic;
                        }
                        .image-cell {
                            padding: 0.5rem;
                        }
                        .image-cell img {
                            max-width: 280px;
                            border-radius: 8px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            transition: transform 0.2s;
                        }
                        .image-cell img:hover {
                            transform: scale(1.05);
                        }
                        .download-btn {
                            background: #1a237e;
                            color: white;
                            padding: 0.8rem 1.5rem;
                            border: none;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 0.9rem;
                            margin: 1rem;
                            
                        }
                        .alert {
                            position: fixed;
                            top: 20px;
                            right: 20px;
                            padding: 15px 20px;
                            background: #4CAF50;
                            color: white;
                            border-radius: 4px;
                            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                            display: none;
                            animation: slideIn 0.3s ease;
                        }
                        @keyframes slideIn {
                            from { transform: translateX(100%); }
                            to { transform: translateX(0); }
                        }
                        @media (max-width: 768px) {
                            body { padding: 1rem; }
                            .header { padding: 1rem; }
                            td, th { padding: 0.75rem; }
                            .image-cell img { max-width: 200px; }
                        }
                    </style>
                    <script>
                    function populateDateDropdown() {
                        // Always recalculate allDates from current rows
                        let allDates = new Set();
                        let allRows = Array.from(document.querySelectorAll("tbody tr[data-date]"));
                        allRows.forEach(row => allDates.add(row.getAttribute("data-date")));
                        const dateSelect = document.getElementById("dateSelect");
                        dateSelect.innerHTML = '<option value="all">All Dates</option>';
                        Array.from(allDates).sort().forEach(date => {
                            dateSelect.innerHTML += `<option value="${date}">${date}</option>`;
                        });
                    }

                    function filterLogs() {
                        // Always get the latest rows
                        let allRows = Array.from(document.querySelectorAll("tbody tr[data-date]"));
                        const date = document.getElementById("dateSelect").value;
                        const search = document.getElementById("searchInput").value.toLowerCase();
                        allRows.forEach(row => {
                            const rowDate = row.getAttribute("data-date");
                            const rowText = row.innerText.toLowerCase();
                            let show = (date === "all" || rowDate === date);
                            if (search) {
                                show = show && rowText.includes(search);
                            }
                            row.style.display = show ? "" : "none";
                        });
                    }

                    // On page load, populate dropdown and filter
                    window.onload = function() {
                        populateDateDropdown();
                        filterLogs();
                        // Add Enter key support for search
                        document.getElementById("searchInput").addEventListener("keyup", function(event) {
                            if (event.key === "Enter") {
                                filterLogs();
                            }
                        });
                    };
                    </script>
                </head>
                <body>
                    <div class="header">
                        <h2>Intrusion Detection Log</h2>
                        <span class="total-count">Total Detections: 0</span>
                        <label for="dateSelect" style="margin-left:2rem;">View by Date:</label>
                        <select id="dateSelect" onchange="filterLogs()" style="margin-right:2rem;"></select>
                        <input id="searchInput" type="text" placeholder="Search by date, time, name..." style="padding:0.5rem; border-radius:4px; border:1px solid #ccc;">
                        <button type="button" class="download-btn" onclick="filterLogs()">Search</button>
                        <button class="download-btn" onclick="downloadData()">Download</button>
                    </div>
                    <script>
                    function showAlert() {
                        const alert = document.getElementById('successAlert');
                        alert.style.display = 'block';
                        setTimeout(() => {
                            alert.style.display = 'none';
                        }, 3000);
                    }
                    function downloadData() {
                        window.location.href = 'download://trigger';
                        return false;
                    }
                    </script>
                    <table>
                        <thead>
                        <tr>
                            <th>S.No</th>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Event</th>
                            <th>Name</th>
                            <th>Evidence</th>
                        </tr>
                        </thead>
                        <tbody>
                """)

        # Create new entry (to be inserted at the top)
        name_display = person_name if person_name else "Unknown"
        name_class = "person-name" if person_name and person_name != "Unknown" else "person-name unknown"
        
        entry = f"""
        <tr data-date="{date_str}">
            <td class="serial">{event_counter}</td>
            <td class="timestamp">{date_str}</td>
            <td class="timestamp">{time_str}</td>
            <td class="event-text">{event}</td>
            <td class="{name_class}">{name_display}</td>
            <td class="image-cell">{"<img src='images/" + os.path.basename(image_path) + "'>" if image_path else "No image"}</td>
        </tr>"""

        # Insert new entry at the top of <tbody>
        with open(LOG_FILE, "r+", encoding='utf-8') as f:
            content = f.read()
            tbody_start = content.find("<tbody>")
            if tbody_start != -1:
                insert_pos = tbody_start + len("<tbody>")
                new_content = content[:insert_pos] + entry + content[insert_pos:]
                # Update total count
                old_count = int(content[content.find("Total Detections: ") + 17:].split("<")[0])
                new_content = new_content.replace(f"Total Detections: {old_count}", f"Total Detections: {event_counter}")
                f.seek(0)
                f.write(new_content)
                f.truncate()
            else:
                # If <tbody> not found, fallback to old method
                f.seek(0, 2)
                f.write(entry + "\n</tbody>\n</table>\n</div>\n</body>\n</html>")
                
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
    