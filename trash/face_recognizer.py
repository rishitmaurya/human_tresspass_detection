def _draw_detections(self, frame):
    frame_height, frame_width = frame.shape[:2]
    scale_x = frame_width / 640
    scale_y = frame_height / 360

    # Draw faces
    for face in self.last_face_results:
        if not isinstance(face, dict) or "location" not in face or "name" not in face:
            continue
        top, right, bottom, left = face["location"]
        # Scale coordinates for display
        top_disp = int(top * scale_y)
        bottom_disp = int(bottom * scale_y)
        left_disp = int(left * scale_x)
        right_disp = int(right * scale_x)
        cv2.rectangle(frame, (left_disp, top_disp), (right_disp, bottom_disp), (0, 255, 255), 2)
        cv2.putText(frame, face["name"], (left_disp, top_disp - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Draw person detections
    current_time = time()
    if self.last_detection_results is not None:
        for person in self.last_detection_results:
            if not isinstance(person, dict) or "box" not in person:
                continue
            box = person["box"]
            if not isinstance(box, (tuple, list)) or len(box) != 4:
                continue

            x1, y1, x2, y2 = box
            # Scale for display
            x1_disp = int(float(x1) * scale_x)
            x2_disp = int(float(x2) * scale_x)
            y1_disp = int(float(y1) * scale_y)
            y2_disp = int(float(y2) * scale_y)

            # Pass original (unscaled) box for matching
            self._handle_person_detection(frame, (x1_disp, y1_disp, x2_disp, y2_disp), current_time, (x1, y1, x2, y2))

    return frame

def _handle_person_detection(self, frame, box, current_time, original_box=None):
    """Handle person detection and ROI intersection"""
    x1, y1, x2, y2 = box
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    # Use original_box for matching (in 640x360 space)
    if original_box is None:
        original_box = box
    ox1, oy1, ox2, oy2 = original_box
    ocenter_x = (ox1 + ox2) // 2
    ocenter_y = (oy1 + oy2) // 2

    # Get face name if any face is detected near this person (in 640x360 space)
    person_name = "Unknown"
    if self.last_face_results:
        for face in self.last_face_results:
            if not isinstance(face, dict) or "location" not in face or "name" not in face:
                continue
            top, right, bottom, left = face["location"]
            face_center_x = (left + right) // 2
            face_center_y = (top + bottom) // 2
            # Match in 640x360 space
            if (ox1 <= face_center_x <= ox2 and oy1 <= face_center_y <= oy2):
                person_name = face["name"]
                break

    # ... rest of your code (unchanged) ...
    # (draw green/red/blue boxes and log as before)