import cv2
import numpy as np
from src.config import Config

class Visualizer:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
    def draw_hud(self, frame, emotion, probs, fps):
        h, w, _ = frame.shape
        
        # 1. Draw Sidebar Background (Semi-transparent)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (300, h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # 2. Draw Title
        cv2.putText(frame, "EMOTION AI", (20, 50), self.font, 1, (255, 255, 255), 2)
        cv2.putText(frame, "v2.0 Pro", (220, 50), self.font, 0.5, Config.THEME_COLOR, 1)
        
        # 3. Draw FPS
        cv2.putText(frame, f"FPS: {int(fps)}", (w - 120, 40), self.font, 0.7, (0, 255, 0), 2)
        
        # 4. Draw Current Emotion (Large)
        color = Config.EMOTION_COLORS.get(emotion, (255, 255, 255))
        cv2.putText(frame, "DETECTED:", (20, 100), self.font, 0.6, (200, 200, 200), 1)
        cv2.putText(frame, emotion.upper(), (20, 150), self.font, 1.5, color, 3)
        
        # 5. Draw Probability Bars
        y_start = 220
        for i, (emo, prob) in enumerate(probs.items()):
            # Label
            cv2.putText(frame, emo.capitalize(), (20, y_start), self.font, 0.6, (220, 220, 220), 1)
            
            # Bar Background
            cv2.rectangle(frame, (100, y_start - 15), (280, y_start + 5), (50, 50, 50), -1)
            
            # Bar Foreground
            bar_width = int(prob * 180)
            bar_color = Config.EMOTION_COLORS.get(emo, (255, 255, 255))
            cv2.rectangle(frame, (100, y_start - 15), (100 + bar_width, y_start + 5), bar_color, -1)
            
            # Percentage
            cv2.putText(frame, f"{int(prob*100)}%", (290, y_start), self.font, 0.5, (255, 255, 255), 1)
            
            y_start += 40
            
        # 6. Draw Developer Info
        cv2.putText(frame, Config.DEV_NAME, (20, h - 40), self.font, 0.5, (150, 150, 150), 1)
        cv2.putText(frame, Config.DEV_WEBSITE, (20, h - 20), self.font, 0.5, (100, 100, 255), 1)

    def draw_face_box(self, frame, face_coords, emotion):
        x, y, w, h = face_coords
        color = Config.EMOTION_COLORS.get(emotion, (255, 255, 255))
        
        # Fancy corners
        l = 30
        t = 2
        
        # Top-Left
        cv2.line(frame, (x, y), (x + l, y), color, t)
        cv2.line(frame, (x, y), (x, y + l), color, t)
        # Top-Right
        cv2.line(frame, (x + w, y), (x + w - l, y), color, t)
        cv2.line(frame, (x + w, y), (x + w, y + l), color, t)
        # Bottom-Left
        cv2.line(frame, (x, y + h), (x + l, y + h), color, t)
        cv2.line(frame, (x, y + h), (x, y + h - l), color, t)
        # Bottom-Right
        cv2.line(frame, (x + w, y + h), (x + w - l, y + h), color, t)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - l), color, t)
