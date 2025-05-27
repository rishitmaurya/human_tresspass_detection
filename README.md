# README.md
# Human Trespass Detection GUI

A Python-based desktop application that uses a live webcam feed to detect human trespassing inside a user-defined workspace area (ROI). Powered by YOLOv8 for real-time human detection, PyQt5 for GUI, and alerting mechanisms including sound and popup notifications.

---

## Features

- Live video stream from webcam with real-time human detection.
- User can mark a rectangular Region of Interest (ROI) on the video.
- Alerts triggered if a human crosses into the ROI:
  - Visual alerts on video feed.
  - Popup alert window.
  - Sound alert.
- Saves snapshot images of trespassing events.
- Logs alerts with timestamps.
- Modular codebase with clean folder structure.

---

## Folder Structure

human_trespass_detection_gui/
│
├── main.py # Entry point to launch the GUI
├── requirements.txt # Python dependencies
├── README.md # Project documentation
│
├── config/
│ └── settings.py # Configurations like model path, thresholds
│
├── gui/
│ ├── app.py # Main PyQt5 app window and logic
│ ├── camera_widget.py # Displays live camera feed in GUI
│ ├── roi_selector.py # ROI drawing support on video frames
│ └── alert_popup.py # Popup window for alerts
│
├── detectors/
│ └── yolo_detector.py # YOLOv8 human detection logic
│
├── utils/
│ ├── geometry.py # ROI containment checks
│ ├── alert.py # Alert sound and GUI triggers
│ └── logger.py # Logs alert events
│
├── assets/
│ ├── alert.mp3 # Alert sound file
│ └── icons/ # Optional icons/images for GUI
│
├── logs/
│ └── alert_log.txt # Auto-generated alert logs
│
├── models/
│ └── yolov8n.pt # YOLOv8 model weights
│
└── output/
└── snapshots/ # Trespass event snapshots

yaml
Copy code

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/human_trespass_detection_gui.git
cd human_trespass_detection_gui
Create and activate a virtual environment (recommended)

bash
Copy code
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
Install dependencies

bash
Copy code
pip install -r requirements.txt
Download YOLOv8 model weights

Download yolov8n.pt from the official YOLOv8 release and place it inside the models/ folder.

Usage
Run the main application:

bash
Copy code
python main.py
Click Start Detection to activate the webcam and begin monitoring.

Use the ROI selector to draw the workspace boundary.

If a human enters the ROI, an alert popup and sound will notify you.

Trespass snapshots are saved automatically in output/snapshots.

Alert logs are stored in logs/alert_log.txt.

Dependencies
Python 3.8+

PyQt5

OpenCV (opencv-python)

Ultralytics YOLOv8 (ultralytics)

numpy

See requirements.txt for the full list.

How It Works
The webcam feed is shown in the GUI.

Users draw a rectangular ROI on the video frame.

Each frame is passed through YOLOv8 to detect humans.

For each detected human, their center point is checked if inside the ROI.

If inside, alert mechanisms trigger: popup, sound, log, and snapshot.

