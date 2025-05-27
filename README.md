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

