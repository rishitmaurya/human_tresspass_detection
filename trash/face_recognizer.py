from deepface import DeepFace
import numpy as np
import faiss
import os
import cv2
from typing import Dict, List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FaceRecognizer:
    def __init__(self, known_faces_dir: str = "known_faces"):
        self.known_faces_dir = known_faces_dir
        self.detector_backend = 'opencv'
        self.model_name = "VGG-Face"
        self.model = None
        self.index = None
        self.face_names = []
        self.embeddings = []
        
        # Initialize model
        try:
            logger.info("Initializing face recognizer...")
            self.model = DeepFace.build_model(self.model_name)
            self.load_known_faces()
            logger.info(f"Loaded {len(self.face_names)} known faces")
        except Exception as e:
            logger.error(f"Error initializing face recognizer: {str(e)}")

    def _extract_embedding(self, embedding_result) -> np.ndarray:
        """Extract embedding vector from DeepFace result"""
        try:
            if isinstance(embedding_result, list):
                logger.debug("Embedding result is a list, taking first element")
                embedding_result = embedding_result[0]
            if isinstance(embedding_result, dict):
                logger.debug("Extracting embedding from dict")
                return np.array(embedding_result.get('embedding', []))
            return np.array(embedding_result)
        except Exception as e:
            logger.error(f"Error extracting embedding: {str(e)}")
            return np.array([])

    def load_known_faces(self):
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir)
            logger.warning(f"Created empty directory: {self.known_faces_dir}")
            return

        logger.info(f"Loading known faces from {self.known_faces_dir}")
        for person_folder in os.listdir(self.known_faces_dir):
            person_path = os.path.join(self.known_faces_dir, person_folder)
            if os.path.isdir(person_path):
                logger.debug(f"Processing person folder: {person_folder}")
                for img_file in os.listdir(person_path):
                    if img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        img_path = os.path.join(person_path, img_file)
                        try:
                            logger.debug(f"Processing image: {img_path}")
                            embedding_result = DeepFace.represent(
                                img_path=img_path,
                                model_name=self.model_name,
                                detector_backend=self.detector_backend,
                                enforce_detection=False
                            )
                            embedding = self._extract_embedding(embedding_result)
                            if embedding.size > 0:
                                self.embeddings.append(embedding)
                                self.face_names.append(person_folder)
                                logger.debug(f"Successfully added face for {person_folder}")
                        except Exception as e:
                            logger.error(f"Error processing {img_path}: {str(e)}")

        if self.embeddings:
            logger.info(f"Building Faiss index with {len(self.embeddings)} embeddings")
            embeddings_array = np.array(self.embeddings).astype('float32')
            d = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(d)
            self.index.add(embeddings_array)
        else:
            logger.warning("No valid embeddings found to build index")

    def recognize_face(self, frame: np.ndarray, face_box: Tuple[int, int, int, int]) -> Optional[str]:
        if self.index is None or not self.face_names:
            logger.warning("Face recognition not initialized properly")
            return None

        try:
            x1, y1, x2, y2 = face_box
            face_img = frame[y1:y2, x1:x2]
            
            temp_path = "temp_face.jpg"
            cv2.imwrite(temp_path, face_img)
            logger.debug(f"Saved temporary face image: {temp_path}")
            
            logger.debug("Getting embedding for detected face")
            embedding_result = DeepFace.represent(
                img_path=temp_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False
            )
            
            os.remove(temp_path)
            logger.debug("Removed temporary face image")
            
            embedding = self._extract_embedding(embedding_result)
            if embedding.size == 0:
                logger.warning("Got empty embedding for detected face")
                return None

            logger.debug("Searching for matching face")
            D, I = self.index.search(np.array([embedding]).astype('float32'), 1)
            
            if D[0][0] < 100:
                person_name = self.face_names[I[0][0]]
                logger.info(f"Found match: {person_name} with distance {D[0][0]}")
                return person_name
            else:
                logger.debug(f"No match found. Best distance was {D[0][0]}")
            
        except Exception as e:
            logger.error(f"Error in face recognition: {str(e)}")
        
        return None
    