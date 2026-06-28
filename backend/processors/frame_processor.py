import cv2
import numpy as np
import time
import mediapipe as mp
from typing import List, Dict, Any, Tuple
from processors.pose_estimator import HeadPoseEstimator
from plugins.face_quality import FaceQualityPlugin
from plugins.emotion import EmotionPlugin
from plugins.blink import BlinkPlugin

class BoundingBoxSmoother:
    """
    Smooths bounding box positions using exponential moving average for stable face tracking.
    """
    def __init__(self, initial_bbox: Tuple[float, float, float, float], smoothing: float = 0.3):
        self.prev_bbox = np.array(initial_bbox, dtype=np.float32)
        self.smoothing = smoothing  # Higher = smoother (less jitter)
    
    def update(self, new_bbox: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """
        Apply exponential smoothing to bounding box.
        smoothing=0.3 means 30% new, 70% previous (smooth)
        smoothing=0.7 means 70% new, 30% previous (responsive)
        """
        new = np.array(new_bbox, dtype=np.float32)
        # EMA: smooth = alpha * new + (1 - alpha) * prev
        smoothed = self.smoothing * new + (1 - self.smoothing) * self.prev_bbox
        self.prev_bbox = smoothed
        return tuple(smoothed.tolist())
    
    def update_smoothing(self, smoothing: float):
        self.smoothing = smoothing


class CentroidTracker:
    """
    Tracks face bounding box centroids across frames to maintain stable Face IDs.
    Now with increased distance threshold for better tracking of fast-moving faces.
    """
    def __init__(self, max_disappeared: int = 10):
        self.next_id = 1
        self.objects = {}  # id -> centroid
        self.disappeared = {}  # id -> missing frame counter
        self.max_disappeared = max_disappeared
        self.velocity = {}  # id -> (vx, vy) for motion prediction

    def register(self, centroid: Tuple[int, int]) -> int:
        self.objects[self.next_id] = centroid
        self.disappeared[self.next_id] = 0
        self.velocity[self.next_id] = (0, 0)
        self.next_id += 1
        return self.next_id - 1

    def deregister(self, object_id: int):
        if object_id in self.objects:
            del self.objects[object_id]
        if object_id in self.disappeared:
            del self.disappeared[object_id]
        if object_id in self.velocity:
            del self.velocity[object_id]

    def update(self, bboxes: List[Tuple[float, float, float, float]]) -> List[int]:
        """
        Updates trackers with list of bounding boxes (x, y, w, h).
        Returns a list of tracking IDs mapping 1:1 with input boxes.
        Uses motion prediction for better tracking of fast-moving faces.
        """
        if not bboxes:
            # Count disappearances for existing objects
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return []

        input_centroids = np.zeros((len(bboxes), 2), dtype=np.int32)
        for i, (x, y, w, h) in enumerate(bboxes):
            input_centroids[i] = (int(x + w / 2), int(y + h / 2))

        if not self.objects:
            assigned_ids = []
            for i in range(len(input_centroids)):
                assigned_ids.append(self.register(tuple(input_centroids[i])))
            return assigned_ids

        object_ids = list(self.objects.keys())
        object_centroids = list(self.objects.values())
        
        # Apply motion prediction (velocity from previous frame)
        predicted_centroids = []
        for i, obj_id in enumerate(object_ids):
            vx, vy = self.velocity.get(obj_id, (0, 0))
            cx, cy = object_centroids[i]
            predicted_centroids.append((cx + vx, cy + vy))
        predicted_centroids = np.array(predicted_centroids, dtype=np.int32)

        # Distance matrix using predicted positions
        D = np.linalg.norm(predicted_centroids[:, np.newaxis] - input_centroids, axis=2)

        # Match rows and columns
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]

        used_rows = set()
        used_cols = set()
        assigned_ids = [None] * len(bboxes)

        for row, col in zip(rows, cols):
            if row in used_rows or col in used_cols:
                continue
                
            # Increased threshold to 300 pixels for better tracking of fast-moving faces
            # Also increase threshold when object has been tracked for a while (higher confidence)
            base_threshold = 300
            confidence_bonus = min(50 * self.disappeared[object_ids[row]], 100)  # Up to +100 for long-tracked faces
            threshold = base_threshold + confidence_bonus
            
            if D[row, col] > threshold:
                continue

            object_id = object_ids[row]
            new_centroid = tuple(input_centroids[col])
            old_centroid = self.objects[object_id]
            
            # Update velocity for next frame prediction (with damping)
            vx = int(new_centroid[0] - old_centroid[0])
            vy = int(new_centroid[1] - old_centroid[1])
            prev_vx, prev_vy = self.velocity[object_id]
            # Blend new velocity with previous (smoothing)
            self.velocity[object_id] = (int(0.7 * vx + 0.3 * prev_vx), int(0.7 * vy + 0.3 * prev_vy))
            
            self.objects[object_id] = new_centroid
            self.disappeared[object_id] = 0
            assigned_ids[col] = object_id
            used_rows.add(row)
            used_cols.add(col)

        # Register unassigned centroids
        for i in range(len(bboxes)):
            if assigned_ids[i] is None:
                assigned_ids[i] = self.register(tuple(input_centroids[i]))

        # Count disappeared for unmatched rows
        unused_rows = set(range(D.shape[0])).difference(used_rows)
        for row in unused_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)

        return assigned_ids

class FrameProcessor:
    """
    Main pipelines orchestrator. Runs MediaPipe Face Mesh, computes spatial pose,
    and forwards detections through FaceQuality, Emotion, and Blink plugins.
    Now includes temporal smoothing for stable bounding box tracking.
    """
    def __init__(self):
        # Initialize MediaPipe Face Mesh (Refined landmarks enables irises)
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=5,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Helper services
        self.pose_estimator = HeadPoseEstimator()
        self.tracker = CentroidTracker(max_disappeared=10)  # Increased for better tracking
        
        # State caches for temporal tracking (allocated per socket connection lifecycle)
        self.history_cache = {}  # face_id -> smoothed probabilities
        self.blink_cache = {}    # face_id -> blink state histories
        self.bbox_smoothers = {}  # face_id -> BoundingBoxSmoother
        
        # Smoothing factor for bbox (0.3 = 30% new, 70% old = smooth)
        self.bbox_smoothing = 0.3
        
        # AI plugins (order matters for Fix 1: BlinkPlugin must run BEFORE EmotionPlugin)
        # so blink_phase is available for eye-based feature substitution
        self.plugins = [
            FaceQualityPlugin(),
            BlinkPlugin(),   # Runs first to set blink_phase
            EmotionPlugin(), # Runs second, consumes blink_phase
        ]

    def close(self):
        self.mp_face_mesh.close()

    def process_frame(self, frame: np.ndarray, config: Dict[str, Any] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Processes a raw frame.
        
        Returns:
            faces: Detailed list of face dictionaries containing box, mesh, metrics, and quality score.
            perf: Processing time diagnostics.
        """
        start_time = time.time()
        
        h, w = frame.shape[:2]
        
        # Update bbox smoothing from config (inverted: higher smoothing slider = smoother bbox)
        if config:
            raw_smoothing = config.get("confidence_smoothing", 0.3)
            # Invert so that UI slider higher = smoother (less responsive bbox)
            self.bbox_smoothing = max(0.15, min(0.6, 1.0 - raw_smoothing))
        
        # MediaPipe expects RGB images
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        mp_start = time.time()
        results = self.mp_face_mesh.process(rgb_frame)
        mp_time = (time.time() - mp_start) * 1000
        
        faces = []
        bboxes = []
        
        # 1. Coordinate parsing
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Convert MediaPipe landmarks to list of [x, y, z] normalized coords
                landmarks_list = [
                    [float(lm.x), float(lm.y), float(lm.z)] 
                    for lm in face_landmarks.landmark
                ]
                
                # Compute pixel bounding box
                xs = [lm[0] * w for lm in landmarks_list[:468]]
                ys = [lm[1] * h for lm in landmarks_list[:468]]
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                
                box_w = x_max - x_min
                box_h = y_max - y_min
                
                # Padding bounding box slightly
                padding_x = box_w * 0.1
                padding_y = box_h * 0.1
                
                raw_bbox = (
                    max(0, x_min - padding_x),
                    max(0, y_min - padding_y),
                    min(w, box_w + 2 * padding_x),
                    min(h, box_h + 2 * padding_y)
                )
                
                bboxes.append(raw_bbox)
                
                # Head pose estimation
                pitch, yaw, roll, distance = self.pose_estimator.estimate_pose(
                    landmarks_list, w, h
                )
                
                faces.append({
                    "raw_bbox": raw_bbox,  # Store raw bbox for smoothing
                    "landmarks": landmarks_list,
                    "pose": {
                        "pitch": pitch,
                        "yaw": yaw,
                        "roll": roll
                    },
                    "distance": distance
                })

        # 2. Tracking ID assignment
        assigned_ids = self.tracker.update(bboxes)
        
        # 3. Apply bounding box smoothing per face
        active_ids = set(assigned_ids)
        for i, (face, face_id) in enumerate(zip(faces, assigned_ids)):
            # Clean up smoothers for disappeared faces
            if face_id not in self.bbox_smoothers:
                self.bbox_smoothers[face_id] = BoundingBoxSmoother(
                    face["raw_bbox"], 
                    self.bbox_smoothing
                )
            
            # Update smoothing factor if changed
            self.bbox_smoothers[face_id].update_smoothing(self.bbox_smoothing)
            
            # Apply smoothing to bbox
            smoothed_bbox = self.bbox_smoothers[face_id].update(face["raw_bbox"])
            face["bbox"] = smoothed_bbox
            face["face_id"] = face_id

        # 4. Running Plugins
        # Setup context arguments for plugins
        plugin_kwargs = {
            "history_cache": self.history_cache,
            "blink_cache": self.blink_cache,
            "alpha": config.get("confidence_smoothing", 0.3) if config else 0.3,
            "model": config.get("model", "ferplus-8") if config else "ferplus-8",
        }
        
        plugin_start = time.time()
        for plugin in self.plugins:
            faces = plugin.process(frame, faces, **plugin_kwargs)
        plugin_time = (time.time() - plugin_start) * 1000

        # Create structured output structure
        output_faces = []
        for face in faces:
            rounded_landmarks = [[round(coord, 4) for coord in pt] for pt in face["landmarks"]]
            
            output_faces.append({
                "face_id": face["face_id"],
                "bbox": [round(float(v), 1) for v in face["bbox"]],
                "landmarks": rounded_landmarks,
                "pose": face["pose"],
                "distance": face["distance"],
                "quality": face["quality"],
                "expression": face.get("expression", "Neutral"),
                "expression_confidence": face.get("expression_confidence", 1.0),
                "all_expressions": face.get("all_expressions", {}),
                "blink_metrics": face.get("blink_metrics", {})
            })

        total_time_ms = (time.time() - start_time) * 1000

        perf_stats = {
            "total_latency_ms": round(total_time_ms, 2),
            "mediapipe_latency_ms": round(mp_time, 2),
            "plugins_latency_ms": round(plugin_time, 2),
            "inference_latency_ms": round(plugin_time, 2)  # approximate
        }

        # Clean old keys from history tracking to prevent memory leaks
        for fid in list(self.history_cache.keys()):
            if fid not in active_ids:
                del self.history_cache[fid]
        for fid in list(self.blink_cache.keys()):
            if fid not in active_ids:
                del self.blink_cache[fid]
        for fid in list(self.bbox_smoothers.keys()):
            if fid not in active_ids:
                del self.bbox_smoothers[fid]

        return output_faces, perf_stats
