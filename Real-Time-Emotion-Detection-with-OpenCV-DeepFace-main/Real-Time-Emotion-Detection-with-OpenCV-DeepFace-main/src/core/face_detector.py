"""
Simple face detector using OpenCV Haar Cascades as fallback
"""
import cv2
import os

class SimpleFaceDetector:
    def __init__(self):
        # Load Haar Cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
    def detect(self, frame):
        """
        Detect faces in frame
        Returns list of face bounding boxes in format (x, y, w, h)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return faces
