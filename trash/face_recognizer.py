# 1. First, modify the update_frame method:
def update_frame(self):
    if not self.cap or not self.cap.isOpened():
        return
        
    try:
        ret, frame = self.cap.read()
        if not ret:
            return
            
        # Process detection every 3rd frame
        self.frame_count += 1
        if self.detection_enabled and self.frame_count % 3 == 0:
            self.detection_manager.process_frame(frame.copy())
        
        # Draw detections from last results
        if self.last_detection_results is not None:
            frame = self._draw_detections(frame)
            
        # Display frame directly (remove _draw_rois call)
        self._display_frame(frame)
        
    except Exception as e:
        print(f"Error in update_frame: {e}")

# 2. Modify the paintEvent method:
def paintEvent(self, event):
    super().paintEvent(event)
    if not hasattr(self, 'video_label'):
        return
        
    painter = QPainter(self.video_label)
    painter.begin(self.video_label)
    
    # Draw normal ROIs in green
    pen = QPen(Qt.green, 2, Qt.SolidLine)
    painter.setPen(pen)
    for roi in self.rois:
        (x1, y1), (x2, y2) = roi
        painter.drawRect(x1, y1, x2 - x1, y2 - y1)
    
    # Draw danger ROIs in red
    pen = QPen(Qt.red, 2, Qt.SolidLine)
    painter.setPen(pen)
    for roi in self.danger_rois:
        (x1, y1), (x2, y2) = roi
        painter.drawRect(x1, y1, x2 - x1, y2 - y1)
    
    # Draw the current ROI being drawn
    if self.current_roi:
        x1, y1, x2, y2 = self.current_roi
        pen = QPen(Qt.red if self.drawing_danger else Qt.green, 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    
    painter.end()

# 3. Remove or comment out the _draw_rois method since we're not using it anymore
# def _draw_rois(self, frame):
#     """Draw warning and danger ROIs on the frame"""
#     ...