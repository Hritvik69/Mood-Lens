import cv2
import numpy as np
from typing import List, Dict, Any
from plugins.base import BasePlugin

class FaceQualityPlugin(BasePlugin):
    """
    Evaluates face image conditions including lighting, blur, centering, 
    and relative distance to output a quality score (0-100) and feedback.
    """
    
    @property
    def name(self) -> str:
        return "face_quality"

    def process(
        self, 
        frame: np.ndarray, 
        faces: List[Dict[str, Any]], 
        **kwargs
    ) -> List[Dict[str, Any]]:
        frame_h, frame_w = frame.shape[:2]
        frame_center_x = frame_w / 2.0
        frame_center_y = frame_h / 2.0
        max_dist = np.sqrt(frame_center_x**2 + frame_center_y**2)
        
        for face in faces:
            bbox = face.get("bbox")  # [x_min, y_min, width, height] in pixel coords
            if not bbox or bbox[2] <= 0 or bbox[3] <= 0:
                # Default empty metrics if no bounding box
                face["quality"] = {
                    "score": 0.0,
                    "lighting": 0.0,
                    "blur": 0.0,
                    "centering": 0.0,
                    "recommendations": ["No face bounding box detected"]
                }
                continue
                
            x, y, w, h = bbox
            # Ensure coordinates are within frame bounds
            x_min, y_min = max(0, int(x)), max(0, int(y))
            x_max, y_max = min(frame_w, int(x + w)), min(frame_h, int(y + h))
            
            face_crop = frame[y_min:y_max, x_min:x_max]
            if face_crop.size == 0:
                face["quality"] = {
                    "score": 0.0,
                    "lighting": 0.0,
                    "blur": 0.0,
                    "centering": 0.0,
                    "recommendations": ["Invalid face crop coordinates"]
                }
                continue
                
            # Convert crop to grayscale for illumination & blur calculations
            gray_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            
            # 1. Lighting Quality (Brightness & Contrast)
            mean_brightness = np.mean(gray_crop)
            std_contrast = np.std(gray_crop)
            
            # Brightness score: Ideal range is 100 - 180
            if 100 <= mean_brightness <= 180:
                lighting_score = 100.0
            elif mean_brightness < 100:
                # Scale from 0 to 100 (60 and below is poor)
                lighting_score = max(0.0, (mean_brightness / 100.0) * 100.0)
            else:
                # Overexposed: scale down above 180
                lighting_score = max(0.0, ((255.0 - mean_brightness) / (255.0 - 180.0)) * 100.0)
                
            # Contrast penalty if too low
            contrast_penalty = 0.0
            if std_contrast < 20.0:
                contrast_penalty = (20.0 - std_contrast) * 2.0  # Max penalty 40
            lighting_score = max(0.0, lighting_score - contrast_penalty)
            
            # 2. Blur Quality (Laplacian Variance)
            # High variance = sharp edges. Low variance = blurry.
            laplacian_var = cv2.Laplacian(gray_crop, cv2.CV_64F).var()
            # Normalize: typical sharp face has variance > 120. Scale variance [0, 120] to [0, 100]
            blur_score = min(100.0, (laplacian_var / 120.0) * 100.0)
            
            # 3. Centering Score
            face_center_x = x + (w / 2.0)
            face_center_y = y + (h / 2.0)
            dist_from_center = np.sqrt(
                (face_center_x - frame_center_x)**2 + 
                (face_center_y - frame_center_y)**2
            )
            # Max distance is from center to corner
            centering_score = max(0.0, (1.0 - (dist_from_center / max_dist)) * 100.0)
            
            # 4. Distance / Sizing Scorer
            # Relate bounding box height to camera frame height
            height_ratio = h / frame_h
            distance_score = 100.0
            distance_feedback = None
            
            if height_ratio < 0.20:
                # Too far
                distance_score = max(0.0, (height_ratio / 0.20) * 100.0)
                distance_feedback = "Move closer to the camera"
            elif height_ratio > 0.80:
                # Too close
                distance_score = max(0.0, ((1.0 - height_ratio) / 0.20) * 100.0)
                distance_feedback = "Move slightly further back"
                
            # Collect Recommendations
            recommendations = []
            if mean_brightness < 70:
                recommendations.append("Improve lighting (too dark)")
            elif mean_brightness > 220:
                recommendations.append("Reduce lighting (too bright / overexposed)")
            if std_contrast < 25:
                recommendations.append("Increase scene contrast")
            if blur_score < 40:
                recommendations.append("Hold still (reduce motion blur)")
            if centering_score < 60:
                recommendations.append("Center your face in the frame")
            if distance_feedback:
                recommendations.append(distance_feedback)
                
            # Aggregate Quality Score
            # Weights: 35% focus/blur, 30% lighting, 20% centering, 15% distance
            final_quality = (
                (blur_score * 0.35) + 
                (lighting_score * 0.30) + 
                (centering_score * 0.20) + 
                (distance_score * 0.15)
            )
            
            # Attach metrics to face metadata
            face["quality"] = {
                "score": round(final_quality, 2),
                "lighting": round(lighting_score, 2),
                "blur": round(blur_score, 2),
                "centering": round(centering_score, 2),
                "recommendations": recommendations if recommendations else ["Face quality optimal"]
            }
            
        return faces
