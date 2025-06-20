def _handle_person_detection(self, frame, box, current_time, original_box=None):
    x1, y1, x2, y2 = box
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    # ... face recognition code ...

    # 1. Check danger zones FIRST
    for roi in self.danger_rois:
        (rx1, ry1), (rx2, ry2) = roi
        if (rx1 <= center_x <= rx2 and ry1 <= center_y <= ry2):
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"Name: {person_name}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            if current_time - self.last_danger_alert_time > 10:
                self.last_danger_alert_time = current_time
                self.handle_danger_alert(frame)
                log_event("Danger Zone Intrusion", frame, person_name)
            return True

    # 2. Check authorization zones
    for roi in getattr(self, "authorization_rois", []):
        (rx1, ry1), (rx2, ry2) = roi
        if (rx1 <= center_x <= rx2 and ry1 <= center_y <= ry2):
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            if person_name == "Unknown":
                if current_time - self.last_authorization_alert_time > 10:
                    self.last_authorization_alert_time = current_time
                    log_event("Authorization Zone Intrusion (Unknown)", frame, person_name)
            return True

    # 3. Check warning zones
    for roi in self.rois:
        (rx1, ry1), (rx2, ry2) = roi
        if (rx1 <= center_x <= rx2 and ry1 <= center_y <= ry2):
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Name: {person_name}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            if current_time - self.last_alert_time > 5:
                self.last_alert_time = current_time
                trigger_alert()
                log_event("Warning Zone Intrusion", frame, person_name)
            return True

    # Not in any zone: draw blue box, NO name label
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
    return False