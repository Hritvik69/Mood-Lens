import time
import numpy as np
from typing import List, Dict, Any
from plugins.base import BasePlugin

class BlinkPlugin(BasePlugin):
    """
    Computes Eye Aspect Ratio (EAR) to detect blinks and drowsiness.
    Also measures eye contact, smile intensity, and mouth openness 
    using precise MediaPipe landmark coordinates.

    Fix 1: Exposes blink_phase per face for EmotionPlugin coupling.
    Blink phase prevents eyelid spring-open overshoot from triggering
    Fear/Surprise during normal blinking.
    """
    
    # MediaPipe eye coordinates (468-477 are irises, if enabled)
    # Right eye landmarks (33: outer corner, 133: inner corner, 159: top, 145: bottom)
    R_EYE_H = (33, 133)
    R_EYE_V1 = (159, 145)
    R_EYE_V2 = (158, 144)
    
    # Left eye landmarks (362: inner corner, 263: outer corner, 386: top, 374: bottom)
    L_EYE_H = (362, 263)
    L_EYE_V1 = (386, 374)
    L_EYE_V2 = (385, 373)
    
    # Irises
    R_IRIS = 468
    L_IRIS = 473
    
    # Mouth landmarks (61: left corner, 291: right corner, 13: inner upper lip, 14: inner lower lip)
    MOUTH_CORNERS = (61, 291)
    INNER_LIPS = (13, 14)
    
    # Reference distance landmarks (outer eye corners: 33, 263)
    OUTER_EYES = (33, 263)
    
    # Configuration
    EAR_THRESHOLD = 0.20
    DROWSINESS_TIME_SEC = 1.5
    
    # Fix 1: Opening phase hold duration (frames)
    # After eyes reopen, hold "opening" phase for this many frames
    # to suppress the spring-open overshoot
    OPENING_HOLD_FRAMES = 2

    @property
    def name(self) -> str:
        return "blink_metrics"

    def dist(self, p1: List[float], p2: List[float]) -> float:
        """Calculates Euclidean distance between two points."""
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def calculate_ear(self, landmarks: List[List[float]], h_idx: tuple, v1_idx: tuple, v2_idx: tuple) -> float:
        """Calculates Eye Aspect Ratio (EAR)."""
        p_h1 = landmarks[h_idx[0]]
        p_h2 = landmarks[h_idx[1]]
        p_v1_top = landmarks[v1_idx[0]]
        p_v1_bottom = landmarks[v1_idx[1]]
        p_v2_top = landmarks[v2_idx[0]]
        p_v2_bottom = landmarks[v2_idx[1]]
        
        v1_dist = self.dist(p_v1_top, p_v1_bottom)
        v2_dist = self.dist(p_v2_top, p_v2_bottom)
        h_dist = self.dist(p_h1, p_h2)
        
        if h_dist == 0:
            return 0.0
        return (v1_dist + v2_dist) / (2.0 * h_dist)

    def process(
        self, 
        frame: np.ndarray, 
        faces: List[Dict[str, Any]], 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Calculates EAR, blinks, eye contact, smile intensity, and mouth openness.
        
        Args:
            frame: Raw frame (used only for aspect ratios if landmarks are normalized).
            faces: List of dictionaries containing "landmarks" (normalized coordinates).
            kwargs: Must contain 'blink_cache' (dict) for tracking state.

        Fix 1: Writes blink_phase per face:
            - "open": eyes are normally open
            - "closing": transitioning from open to closed
            - "closed": eyes are closed
            - "opening": 1-2 frames after eyes reopen (suppresses spring-open overshoot)
        """
        if not faces:
            return faces
            
        blink_cache = kwargs.get("blink_cache", {})
        current_time = time.time()
        
        for face in faces:
            landmarks = face.get("landmarks")
            if not landmarks or len(landmarks) < 468:
                continue
                
            face_id = face.get("face_id", 0)
            
            # Initialize blink state cache for this face if not present
            if face_id not in blink_cache:
                blink_cache[face_id] = {
                    "eyes_closed": False,
                    "closed_time_start": None,
                    "blink_timestamps": [],
                    "drowsiness_detected": False,
                    # Fix 1: Blink phase tracking
                    "blink_phase": "open",
                    "opening_hold_counter": 0,
                }
            cache = blink_cache[face_id]
            
            # 1. EAR Calculations
            ear_r = self.calculate_ear(landmarks, self.R_EYE_H, self.R_EYE_V1, self.R_EYE_V2)
            ear_l = self.calculate_ear(landmarks, self.L_EYE_H, self.L_EYE_V1, self.L_EYE_V2)
            avg_ear = (ear_r + ear_l) / 2.0
            
            # 2. Blink Detection & Drowsiness Tracker
            is_closed = avg_ear < self.EAR_THRESHOLD
            
            # Fix 1: Track blink phase transitions
            prev_closed = cache["eyes_closed"]
            
            if is_closed:
                if not prev_closed:
                    # Transition from open to closing
                    cache["eyes_closed"] = True
                    cache["closed_time_start"] = current_time
                    cache["blink_phase"] = "closing"
                    cache["opening_hold_counter"] = 0
                else:
                    # Stays closed
                    cache["blink_phase"] = "closed"
                    # Check duration for drowsiness
                    closed_duration = current_time - cache["closed_time_start"]
                    if closed_duration >= self.DROWSINESS_TIME_SEC:
                        cache["drowsiness_detected"] = True
            else:
                if prev_closed:
                    # Transition from closed to open: register blink
                    cache["eyes_closed"] = False
                    cache["drowsiness_detected"] = False
                    # Only count blinks that were short (not drowsiness)
                    closed_duration = current_time - cache["closed_time_start"]
                    if closed_duration < self.DROWSINESS_TIME_SEC:
                        cache["blink_timestamps"].append(current_time)
                    cache["closed_time_start"] = None
                    # Fix 1: Enter "opening" phase for spring-open suppression
                    cache["blink_phase"] = "opening"
                    cache["opening_hold_counter"] = self.OPENING_HOLD_FRAMES
                else:
                    # Fix 1: Count down opening hold counter
                    if cache.get("opening_hold_counter", 0) > 0:
                        cache["opening_hold_counter"] -= 1
                        cache["blink_phase"] = "opening"
                    else:
                        cache["blink_phase"] = "open"
                        
            # Keep only blinks within the last 60 seconds
            cache["blink_timestamps"] = [
                t for t in cache["blink_timestamps"] if current_time - t <= 60.0
            ]
            blink_rate = len(cache["blink_timestamps"]) # Blinks per minute (BPM)
            
            # 3. Eye Contact Detection
            # Check iris position relative to horizontal eye corners
            # Right Eye: Corner 1 (33) -> Corner 2 (133). Iris: 468
            p_rh1 = landmarks[self.R_EYE_H[0]]
            p_rh2 = landmarks[self.R_EYE_H[1]]
            p_riris = landmarks[self.R_IRIS]
            
            p_lh1 = landmarks[self.L_EYE_H[0]]
            p_lh2 = landmarks[self.L_EYE_H[1]]
            p_liris = landmarks[self.L_IRIS]
            
            # Compute horizontal ratio: dist(Corner1, Iris) / dist(Corner1, Corner2)
            rh_dist_full = self.dist(p_rh1, p_rh2)
            lh_dist_full = self.dist(p_lh1, p_lh2)
            
            rh_ratio = self.dist(p_rh1, p_riris) / rh_dist_full if rh_dist_full > 0 else 0.5
            lh_ratio = self.dist(p_lh1, p_liris) / lh_dist_full if lh_dist_full > 0 else 0.5
            
            # Eye contact means iris is centered horizontally (between 0.40 and 0.60)
            # and eyes are open (not blinking)
            has_eye_contact = False
            if not is_closed:
                if 0.40 <= rh_ratio <= 0.60 and 0.40 <= lh_ratio <= 0.60:
                    has_eye_contact = True
                    
            # 4. Smile Intensity Estimation
            # Distance between mouth corners normalized by outer eye distance
            p_m1 = landmarks[self.MOUTH_CORNERS[0]]
            p_m2 = landmarks[self.MOUTH_CORNERS[1]]
            p_e1 = landmarks[self.OUTER_EYES[0]]
            p_e2 = landmarks[self.OUTER_EYES[1]]
            
            mouth_w = self.dist(p_m1, p_m2)
            eye_w = self.dist(p_e1, p_e2)
            
            smile_ratio = mouth_w / eye_w if eye_w > 0 else 0.0
            
            # Normalize smile intensity: baseline is ~0.65, full smile is ~0.90
            # Map 0.65 -> 0% and 0.90 -> 100%
            smile_intensity = max(0.0, min(100.0, ((smile_ratio - 0.65) / (0.90 - 0.65)) * 100.0))
            
            # 5. Mouth Openness
            # Vertical inner lip distance normalized by outer eye distance
            p_u = landmarks[self.INNER_LIPS[0]]
            p_d = landmarks[self.INNER_LIPS[1]]
            
            lip_dist = self.dist(p_u, p_d)
            mouth_open_ratio = lip_dist / eye_w if eye_w > 0 else 0.0
            
            # Normalize mouth openness: baseline is ~0.02 (closed), open is ~0.35
            mouth_openness = max(0.0, min(100.0, ((mouth_open_ratio - 0.02) / (0.35 - 0.02)) * 100.0))
            
            # Inject results into face dictionary
            face["blink_metrics"] = {
                "ear": round(float(avg_ear), 3),
                "blink_rate": blink_rate,
                "drowsiness_detected": cache["drowsiness_detected"],
                "eye_contact": has_eye_contact,
                "smile_intensity": round(smile_intensity, 1),
                "mouth_openness": round(mouth_openness, 1)
            }
            
            # Fix 1: Expose blink_phase for EmotionPlugin coupling
            face["blink_phase"] = cache["blink_phase"]
            
        return faces
