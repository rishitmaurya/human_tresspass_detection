import os
from datetime import datetime
import cv2

LOG_FILE = os.path.join("logs", "alert_log.html")
IMAGES_DIR = os.path.join("logs", "images")
event_counter = 0

def log_event(event, frame=None):
    """
    Appends an event to the alert log with timestamp and image if provided.

    Args:
        event (str): Description of the event
        frame (numpy.ndarray, optional): The image frame to save
    """
    global event_counter
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
            </head>
            
            <body>
                <div class="alert" id="successAlert">CSV Downloaded Successfully!</div>
                <div class="container">
                    <div class="header">
                        <h2>Intrusion Detection Log</h2>
                        <span class="total-count">Total Detections: 0</span>
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
                        // Use QtWebChannel to communicate with Python
                        window.location.href = 'download://trigger';
                        return false;
                    }
                    
                    </script>
                    <table>
                        <tr>
                            <th>S.No</th>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Event</th>
                            <th>Evidence</th>
                        </tr>
            """)

    # Create new entry (to be inserted at the top)
    entry = f"""
    <tr>
        <td class="serial">{event_counter}</td>
        <td class="timestamp">{date_str}</td>
        <td class="timestamp">{time_str}</td>
        <td class="event-text">{event}</td>
        <td class="image-cell">{"<img src='images/" + os.path.basename(image_path) + "'>" if image_path else "No image"}</td>
    </tr>"""

    # Modified to insert new entries at the top
    with open(LOG_FILE, "r+", encoding='utf-8') as f:
        content = f.read()
        table_start = content.find("<tr>\n                            <th")
        if table_start != -1:
            # Find the position after the header row
            insert_pos = content.find("</tr>", table_start) + 5
            # Update total count
            old_count = int(content[content.find("Total Detections: ") + 17:].split("<")[0])
            new_content = content[:insert_pos] + entry + content[insert_pos:]
            new_content = new_content.replace(f"Total Detections: {old_count}", f"Total Detections: {event_counter}")
            f.seek(0)
            f.write(new_content)
            f.truncate()
        else:
            f.seek(0, 2)
            f.write(entry + "\n</table>\n</div>\n</body>\n</html>")