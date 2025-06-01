import face_recognition
import cv2
import numpy as np
import os
import pickle
import logging
from typing import List, Tuple, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceRecognizer:
    def __init__(self, known_faces_dir: str = "known_faces", cache_file: str = "known_faces.pkl"):
        """Initialize face recognizer with known faces directory"""
        self.known_faces_dir = known_faces_dir
        self.cache_file = cache_file
        self.known_encodings = []
        self.known_names = []
        
        # Load or create face encodings
        self._initialize_known_faces()
    
    def _initialize_known_faces(self):
        """Load face encodings from cache or create new ones"""
        if os.path.exists(self.cache_file):
            logger.info("Loading cached face encodings...")
            try:
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_encodings = data['encodings']
                    self.known_names = data['names']
                logger.info(f"Loaded {len(self.known_names)} faces from cache")
                return
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        
        self._load_face_encodings()

    def _load_face_encodings(self):
        """Load and encode all known faces from directory"""
        logger.info("Loading face encodings from images...")
        
        for person_folder in os.listdir(self.known_faces_dir):
            folder_path = os.path.join(self.known_faces_dir, person_folder)
            
            if not os.path.isdir(folder_path):
                continue
                
            logger.info(f"Processing faces for: {person_folder}")
            
            for image_file in os.listdir(folder_path):
                if not image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                    
                image_path = os.path.join(folder_path, image_file)
                try:
                    # Load and encode face
                    face_image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(face_image)
                    
                    if encodings:
                        self.known_encodings.append(encodings[0])
                        self.known_names.append(person_folder)
                        logger.debug(f"Added face from {image_file}")
                    else:
                        logger.warning(f"No face found in {image_file}")
                        
                except Exception as e:
                    logger.error(f"Error processing {image_file}: {e}")
        
        # Save to cache
        if self.known_encodings:
            try:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump({
                        'encodings': self.known_encodings,
                        'names': self.known_names
                    }, f)
                logger.info(f"Cached {len(self.known_names)} face encodings")
            except Exception as e:
                logger.error(f"Error saving cache: {e}")

    def recognize_face(self, frame: np.ndarray, face_location: Tuple[int, int, int, int]) -> Optional[str]:
        """Recognize a face in the given location of the frame"""
        if not self.known_encodings:
            return None
            
        try:
            # Extract face encoding
            top, right, bottom, left = face_location
            face_encoding = face_recognition.face_encodings(
                frame,
                [(top, right, bottom, left)]
            )
            
            if not face_encoding:
                return None
                
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.known_encodings,
                face_encoding[0],
                tolerance=0.6  # Adjust this value for stricter/looser matching
            )
            
            if True in matches:
                return self.known_names[matches.index(True)]
                
        except Exception as e:
            logger.error(f"Error in face recognition: {e}")
            
        return None

    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect all faces in the frame"""
        # Resize frame for faster face detection
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Find all faces in the frame
        face_locations = face_recognition.face_locations(small_frame)
        
        # Scale back up face locations
        return [(
            int(top * 4), int(right * 4), 
            int(bottom * 4), int(left * 4)
        ) for top, right, bottom, left in face_locations]