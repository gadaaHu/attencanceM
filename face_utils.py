import face_recognition
import cv2
import numpy as np
import pickle
import os
from datetime import datetime
import database

class AdvancedFaceRecognition:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all known face encodings from database"""
        conn = database.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT id, fullname, face_encoding_path FROM members WHERE face_encoding_path IS NOT NULL AND status = 'active'")
            members = cursor.fetchall()
            
            for member in members:
                encoding_path = member['face_encoding_path']
                if os.path.exists(encoding_path):
                    with open(encoding_path, 'rb') as f:
                        face_encoding = pickle.load(f)
                    
                    self.known_face_encodings.append(face_encoding)
                    self.known_face_ids.append(member['id'])
                    self.known_face_names.append(member['fullname'])
            
            print(f"✅ Loaded {len(self.known_face_ids)} known faces")
        except Exception as e:
            print(f"❌ Error loading known faces: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def recognize_faces(self, image):
        """Recognize faces in the given image with confidence scores"""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            recognized_members = []
            
            for face_encoding in face_encodings:
                if len(self.known_face_encodings) == 0:
                    continue
                
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                best_distance = face_distances[best_match_index]
                confidence = 1 - best_distance
                
                if confidence > 0.6:
                    recognized_members.append((self.known_face_ids[best_match_index], confidence))
            
            return recognized_members
        except Exception as e:
            print(f"❌ Error in face recognition: {e}")
            return []

# Global instance
face_system = AdvancedFaceRecognition()

def encode_and_save_face(image_path, member_id):
    """Encode face from image and save encoding"""
    try:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) > 0:
            encoding_path = f"known_faces/member_{member_id}.pkl"
            with open(encoding_path, 'wb') as f:
                pickle.dump(face_encodings[0], f)
            
            face_system.load_known_faces()
            return encoding_path
        else:
            return None
    except Exception as e:
        print(f"❌ Error encoding face: {e}")
        return None

def recognize_faces(image):
    """Recognize faces in image using the global system"""
    return face_system.recognize_faces(image)

def allowed_file(filename):
    """Check if file type is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'bmp'}