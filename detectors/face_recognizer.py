import face_recognition
import cv2
import os
import numpy as np

class FaceRecognizer:
    def __init__(self, known_faces_dir="known_faces", tolerance=0.4):
        self.known_faces_dir = known_faces_dir
        self.tolerance = tolerance
        self.known_encodings = []
        self.known_names = []
        self.load_known_faces()

    def load_known_faces(self):
        self.known_encodings = []
        self.known_names = []
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir)
        for name in os.listdir(self.known_faces_dir):
            person_dir = os.path.join(self.known_faces_dir, name)
            if not os.path.isdir(person_dir):
                continue
            for filename in os.listdir(person_dir):
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                filepath = os.path.join(person_dir, filename)
                try:
                    # Load image using face_recognition (expects RGB)
                    image = face_recognition.load_image_file(filepath)
                    if image is None or len(image.shape) != 3 or image.shape[2] != 3:
                        print(f"Skipping file (not RGB image): {filepath}")
                        continue
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        self.known_encodings.append(encodings[0])
                        self.known_names.append(name)
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    def recognize_faces(self, frame):
        # Ensure frame is a valid 8-bit 3-channel image
        if frame is None:
            return []
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            return []

        # Increased frame size for better face recognition accuracy
        small_frame = cv2.resize(frame, (320, 240))  # Increased from 160x120
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        try:
            # Use faster face detection model
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            
            if not face_locations:
                return []
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            results = []
            
            # Scale factor to convert back to original frame size
            scale_x = frame.shape[1] / 320
            scale_y = frame.shape[0] / 240
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Scale coordinates back to original frame size
                top = int(top * scale_y)
                right = int(right * scale_x)
                bottom = int(bottom * scale_y)
                left = int(left * scale_x)
            
                name = "Unknown"
                if len(self.known_encodings) > 0:
                    # Use faster comparison with balanced tolerance
                    matches = face_recognition.compare_faces(
                        self.known_encodings, 
                        face_encoding, 
                        tolerance=0.45  # Balanced tolerance for accuracy and speed
                    )
                    if True in matches:
                        face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = self.known_names[best_match_index]
            
                results.append({
                    "name": name,
                    "location": (top, right, bottom, left)
                })
            return results
        except Exception as e:
            print(f"Error in face recognition: {str(e)}")
            return []