import os
import cv2
import numpy as np
import threading
from deepface import DeepFace
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from src.config import Config

class EmotionAnalyzer:
    def __init__(self):
        self.deepface_model = "liveness" # DeepFace handles its own models
        self.custom_model = None
        self.load_custom_model()
        
        self.current_emotion = "neutral"
        self.emotion_probs = {e: 0.0 for e in Config.EMOTIONS}
        self.lock = threading.Lock()
        self.running = False

    def load_custom_model(self):
        try:
            if os.path.exists(Config.MODEL_PATH):
                self.custom_model = load_model(Config.MODEL_PATH, compile=False)
                print("✅ Custom FER Model Loaded.")
            else:
                print(f"⚠️ Custom model not found at {Config.MODEL_PATH}. Using DeepFace only.")
        except Exception as e:
            print(f"❌ Error loading custom model: {e}")

    def start(self):
        self.running = True
        
    def stop(self):
        self.running = False

    def analyze(self, face_img):
        """
        Runs analysis in a separate thread to avoid blocking the UI.
        """
        if not self.running: return
        
        threading.Thread(target=self._analyze_thread, args=(face_img,)).start()

    def _analyze_thread(self, face_img):
        if face_img is None or face_img.size == 0: return

        try:
            # 1. Custom Model Analysis (Fast)
            custom_probs = {}
            if self.custom_model:
                roi = cv2.resize(face_img, (48, 48))
                roi = roi.astype("float") / 255.0
                roi = img_to_array(roi)
                roi = np.expand_dims(roi, axis=0)
                
                preds = self.custom_model.predict(roi, verbose=0)[0]
                custom_probs = {label: float(prob) for label, prob in zip(Config.EMOTIONS, preds)}

            # 2. DeepFace Analysis (Accurate but Slower)
            # We can skip DeepFace every few frames or run it less frequently if needed
            # For now, let's rely on the custom model for speed if available, 
            # or use DeepFace if custom model is missing.
            
            final_probs = custom_probs
            
            if not final_probs: # Fallback to DeepFace if no custom model
                try:
                    # DeepFace expects BGR
                    result = DeepFace.analyze(face_img, actions=['emotion'], enforce_detection=False, silent=True)
                    if result and isinstance(result, list) and len(result) > 0:
                        emotion_data = result[0].get('emotion', {})
                        # Normalize keys to lowercase and convert to 0-1 range
                        final_probs = {k.lower(): float(v)/100.0 for k, v in emotion_data.items()}
                except Exception as e:
                    print(f"DeepFace analysis error: {e}")
                    pass

            # Update State
            if final_probs:
                with self.lock:
                    self.emotion_probs = final_probs
                    self.current_emotion = max(final_probs, key=final_probs.get)

        except Exception as e:
            print(f"Analysis Error: {e}")

    def get_results(self):
        with self.lock:
            return self.current_emotion, self.emotion_probs
