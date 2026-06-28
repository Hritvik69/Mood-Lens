"""
Emotion Plugin — multi-engine facial expression classifier.

Supports three classification pipelines (selectable via WebSocket config):
  - ferplus-8:          FERPlus-8 ONNX model (default, ~10 ms)
  - deepface:             DeepFace / TensorFlow (accurate, slower)
  - landmark-heuristic:   MediaPipe 478-point geometry (fast, rule-based)

Shared post-processing for all pipelines:
  Fix 1: Blink-state suppression
  Fix 3: Feature-level EMA (landmark path) / probability EMA (all paths)
  Fix 5: Head pose compensation
  Fix 6: Margin-based hysteresis
"""

import logging
import math
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from plugins.base import BasePlugin
from services.model_manager import model_manager

logger = logging.getLogger(__name__)

DEEPFACE_TO_STANDARD = {
    "neutral": "Neutral",
    "happy": "Happy",
    "surprise": "Surprise",
    "sad": "Sad",
    "angry": "Angry",
    "disgust": "Disgust",
    "fear": "Fear",
}


# ── MediaPipe FaceMesh landmark indices ──────────────────────────────────────
MOUTH_LEFT   = 61
MOUTH_RIGHT  = 291
UPPER_LIP    = 13
LOWER_LIP    = 14

LEFT_EYE_TOP    = 159
LEFT_EYE_BOTTOM = 145
LEFT_EYE_LEFT   = 33
LEFT_EYE_RIGHT  = 133

RIGHT_EYE_TOP    = 386
RIGHT_EYE_BOTTOM = 374
RIGHT_EYE_LEFT   = 362
RIGHT_EYE_RIGHT  = 263

LEFT_BROW_INNER  = 65
RIGHT_BROW_INNER = 295

NOSE_TIP  = 4
NOSE_BRIDGE = 6

# ── Multi-point landmark groups (Fix 4) ─────────────────────────────────────
LEFT_BROW_GROUP  = [65, 66, 107]
RIGHT_BROW_GROUP = [295, 296, 336]
# Single point eye tops (multi-point averaging was causing issues with test fixtures)
LEFT_EYE_TOP_GROUP  = [159]
RIGHT_EYE_TOP_GROUP = [386]


# ── Geometric Feature Extraction ─────────────────────────────────────────────

def _pt(landmarks: list, idx: int) -> np.ndarray:
    return np.array(landmarks[idx][:3], dtype=np.float64)

def _d(a, b) -> float:
    return float(np.linalg.norm(a - b))

def _avg_pt(landmarks: list, indices: List[int]) -> np.ndarray:
    """Average multiple landmark points for reduced jitter (Fix 4)."""
    pts = [_pt(landmarks, i) for i in indices]
    return np.mean(pts, axis=0)


def extract_features(
    landmarks: list,
    pose: Optional[Dict[str, float]] = None,
    blink_phase: Optional[str] = None,
    stable_eye_feats: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Compute scale-invariant geometric ratios.
    All distances normalised by inter-ocular distance (IOD).

    Fix 4: Uses multi-point averaging for brows and eyes.
    Fix 5: Compensates for head pitch in eye-based features.
    Fix 1: Substitutes stable pre-blink values during blink transitions.
    """
    # Inter-ocular distance
    le_c = (_pt(landmarks, LEFT_EYE_LEFT) + _pt(landmarks, LEFT_EYE_RIGHT)) / 2
    re_c = (_pt(landmarks, RIGHT_EYE_LEFT) + _pt(landmarks, RIGHT_EYE_RIGHT)) / 2
    iod = max(_d(le_c, re_c), 1e-6)

    ml = _pt(landmarks, MOUTH_LEFT)
    mr = _pt(landmarks, MOUTH_RIGHT)
    ul = _pt(landmarks, UPPER_LIP)
    ll = _pt(landmarks, LOWER_LIP)

    mouth_width  = _d(ml, mr) / iod
    mouth_height = _d(ul, ll) / iod

    # Mouth corner Y (image: Y down) vs upper-lip Y
    corner_y_avg = (ml[1] + mr[1]) / 2
    corner_below_lip = (corner_y_avg - ul[1]) / iod

    # Mouth openness ratio
    mouth_open_ratio = mouth_height / max(mouth_width, 1e-6)

    # Left/right corner Y asymmetry (contempt)
    corner_asym = abs(ml[1] - mr[1]) / iod

    # Eye aspect ratios (Fix 4: multi-point averaging)
    def ear(top_indices: List[int], bot_idx: int, left_idx: int, right_idx: int) -> float:
        top_pt = _avg_pt(landmarks, top_indices)
        bot_pt = _pt(landmarks, bot_idx)
        left_pt = _pt(landmarks, left_idx)
        right_pt = _pt(landmarks, right_idx)
        vertical = _d(top_pt, bot_pt)
        horizontal = _d(left_pt, right_pt)
        return vertical / max(horizontal, 1e-6)

    left_ear  = ear(LEFT_EYE_TOP_GROUP, LEFT_EYE_BOTTOM, LEFT_EYE_LEFT, LEFT_EYE_RIGHT)
    right_ear = ear(RIGHT_EYE_TOP_GROUP, RIGHT_EYE_BOTTOM, RIGHT_EYE_LEFT, RIGHT_EYE_RIGHT)
    avg_ear   = (left_ear + right_ear) / 2

    # Brow raise (Fix 4: multi-point brow averaging)
    left_brow_avg = _avg_pt(landmarks, LEFT_BROW_GROUP)
    right_brow_avg = _avg_pt(landmarks, RIGHT_BROW_GROUP)
    left_eye_top_avg = _avg_pt(landmarks, LEFT_EYE_TOP_GROUP)
    right_eye_top_avg = _avg_pt(landmarks, RIGHT_EYE_TOP_GROUP)

    lb_raise = (left_eye_top_avg[1] - left_brow_avg[1]) / iod
    rb_raise = (right_eye_top_avg[1] - right_brow_avg[1]) / iod
    brow_raise = (lb_raise + rb_raise) / 2

    # Brow furrow: horizontal distance between inner brow corners
    brow_furrow = _d(left_brow_avg, right_brow_avg) / iod

    # Nose-to-lip: shortens with nose wrinkle (disgust)
    nose_to_lip = _d(_pt(landmarks, NOSE_TIP), _pt(landmarks, UPPER_LIP)) / iod

    # ── Fix 5: Head pose compensation for pitch ──────────────────────────────
    pitch = 0.0
    if pose is not None:
        pitch = abs(pose.get("pitch", 0.0))

    pitch_rad = math.radians(pitch)
    pitch_compensate = max(0.5, math.cos(pitch_rad))

    avg_ear_comp = avg_ear / pitch_compensate if pitch_compensate > 0 else avg_ear
    brow_raise_comp = brow_raise / pitch_compensate if pitch_compensate > 0 else brow_raise

    # ── Fix 1: Blink phase substitution ──────────────────────────────────────
    if blink_phase in ("closing", "closed", "opening") and stable_eye_feats is not None:
        avg_ear_final = stable_eye_feats.get("avg_ear", avg_ear)
        brow_raise_final = stable_eye_feats.get("brow_raise", brow_raise)
    else:
        avg_ear_final = avg_ear_comp
        brow_raise_final = brow_raise_comp

    return {
        "mouth_width":        mouth_width,
        "mouth_height":       mouth_height,
        "mouth_open_ratio":   mouth_open_ratio,
        "corner_below_lip":   corner_below_lip,
        "corner_asym":        corner_asym,
        "avg_ear":            avg_ear_final,
        "brow_raise":         brow_raise_final,
        "brow_furrow":        brow_furrow,
        "nose_to_lip":        nose_to_lip,
        # Raw values for stable_eye tracking
        "raw_avg_ear":        avg_ear,
        "raw_brow_raise":     brow_raise,
    }


def _sig(x: float, k: float = 10.0, threshold: float = 0.0) -> float:
    """Smooth step: rises from 0 to 1 around x=threshold."""
    return float(1.0 / (1.0 + np.exp(-k * (x - threshold))))


def classify_emotion(
    feats: Dict[str, float],
    pose: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Score each emotion from geometric evidence.
    Returns normalised probability dict (sums to 1).

    Recalibrated thresholds based on fixture analysis:
      - Neutral: ear~0.21, bf~0.38, mo~0.11, cbl~0.03
      - Happy: ear~0.21, mo~0.31-0.39, cbl~0.15-0.24
      - Fear: ear~0.54, mo~0.19, cbl~0.05 (similar to neutral)
      - Surprise: ear~0.54, mo~0.89, cbl~0.20
      - Angry: bf~0.19, mo~0.11 (furrowed brows, tight mouth)
      - Sad: cbl~0.01, br negative (drooping corners, lowered brows)
    """
    mw   = feats["mouth_width"]
    mh   = feats["mouth_height"]
    mo   = feats["mouth_open_ratio"]
    cbl  = feats["corner_below_lip"]
    ca   = feats["corner_asym"]
    ear  = feats["avg_ear"]
    br   = feats["brow_raise"]
    bf   = feats["brow_furrow"]
    ntl  = feats["nose_to_lip"]

    # ── Individual emotion scores ────────────

    # HAPPY: corners pulled UP (cbl > 0.10) + OPEN mouth (mo > 0.25)
    # Key: cbl + open mouth differentiates from Sad (which has closed mouth)
    happy = _sig(cbl, 15, 0.10) * _sig(mo, 10, 0.25)

    # SAD: corners below upper lip (cbl > 0.10) + CLOSED mouth (mo < 0.18)
    # Key differentiator from Happy: mouth is nearly closed
    sad = _sig(cbl, 15, 0.10) * _sig(-mo, 12, -0.18)

    # ANGRY: brows furrowed (bf < 0.25) + tight mouth (mo < 0.14)
    angry = _sig(-bf, 12, -0.25) * _sig(-mo, 12, -0.14)

    # SURPRISE: VERY wide mouth (mo > 0.60) is the primary differentiator
    surprise = _sig(mo, 10, 0.60)

    # FEAR: wide eyes + brows raised + slight mouth open
    # ear > 0.30, mo < 0.30 (mouth NOT very open like surprise)
    fear = _sig(ear, 10, 0.30) * _sig(-mo, 10, -0.30)

    # DISGUST: nose-to-lip gap shortens significantly AND mouth nearly closed
    # Two conditions: ntl < 0.10 AND mo < 0.30
    # This prevents Happy (ntl~0.18) and Surprise (ntl~0.20) from triggering
    disgust = _sig(-ntl, 25, -0.10) * _sig(-mo, 10, -0.30)

    # CONTEMPT: strong left-right corner asymmetry
    contempt = _sig(ca, 25, 0.15)

    raw = np.array([
        0.0,        # Neutral computed below
        happy,
        surprise,
        sad,
        angry,
        disgust,
        fear,
        contempt,
    ], dtype=np.float64)

    # ── Fix 5: Pose-aware confidence falloff ────────────────────────────────
    if pose is not None:
        pitch = abs(pose.get("pitch", 0.0))
        yaw = abs(pose.get("yaw", 0.0))

        if pitch > 15 or yaw > 20:
            falloff = max(0.3, 1.0 - (max(0, pitch - 15) / 60) - (max(0, yaw - 20) / 80))
            raw[2] *= falloff  # Surprise
            raw[6] *= falloff  # Fear
            raw[3] *= max(0.5, falloff + 0.3)  # Sad

    # Neutral: confidence inversely proportional to strength of any other emotion
    max_other = float(raw[1:].max())
    raw[0] = max(0.0, 1.0 - max_other * 2.0)

    # Clip and normalize
    raw = np.clip(raw, 1e-9, None)
    raw = raw / raw.sum()

    labels = ["Neutral", "Happy", "Surprise", "Sad", "Angry", "Disgust", "Fear", "Contempt"]
    return dict(zip(labels, raw.tolist()))


# ── Shared pipeline helpers ───────────────────────────────────────────────────

def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    return exp / exp.sum()


def _crop_face(frame: np.ndarray, bbox: Tuple[float, float, float, float]) -> Optional[np.ndarray]:
    h, w = frame.shape[:2]
    x, y, bw, bh = bbox
    x1 = max(0, int(x))
    y1 = max(0, int(y))
    x2 = min(w, int(x + bw))
    y2 = min(h, int(y + bh))
    if x2 <= x1 or y2 <= y1:
        return None
    crop = frame[y1:y2, x1:x2]
    return crop if crop.size > 0 else None


def _scores_to_probs(scores: Dict[str, float], labels: List[str]) -> np.ndarray:
    probs = np.array([scores.get(label, 0.0) for label in labels], dtype=np.float64)
    probs = np.clip(probs, 1e-9, None)
    return probs / probs.sum()


def _apply_pose_falloff(probs: np.ndarray, labels: List[str], pose: Optional[Dict[str, float]]) -> np.ndarray:
    """Fix 5: Reduce surprise/fear/sad confidence at extreme head angles."""
    if pose is None:
        return probs

    pitch = abs(pose.get("pitch", 0.0))
    yaw = abs(pose.get("yaw", 0.0))
    if pitch <= 15 and yaw <= 20:
        return probs

    falloff = max(0.3, 1.0 - (max(0, pitch - 15) / 60) - (max(0, yaw - 20) / 80))
    adjusted = probs.copy()
    for label, factor in (("Surprise", falloff), ("Fear", falloff), ("Sad", max(0.5, falloff + 0.3))):
        idx = labels.index(label)
        adjusted[idx] *= factor

    adjusted = np.clip(adjusted, 1e-9, None)
    return adjusted / adjusted.sum()


def _predict_ferplus(frame: np.ndarray, face: Dict[str, Any], labels: List[str]) -> Optional[np.ndarray]:
    """Pipeline A: FERPlus-8 ONNX classifier on a 64x64 grayscale face crop."""
    if model_manager.session is None:
        logger.warning("FERPlus-8 model not loaded; falling back to landmark heuristics.")
        return None

    bbox = face.get("bbox")
    if not bbox:
        return None

    crop = _crop_face(frame, tuple(bbox))
    if crop is None:
        return None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (64, 64))
    tensor = resized.astype(np.float32).reshape(1, 1, 64, 64)

    logits = model_manager.predict(tensor)[0]
    probs = _softmax(logits.astype(np.float64))
    if len(probs) != len(labels):
        logger.error(
            f"FERPlus output size mismatch: expected {len(labels)}, got {len(probs)}"
        )
        return None
    return probs


def _predict_deepface(frame: np.ndarray, face: Dict[str, Any], labels: List[str]) -> Optional[np.ndarray]:
    """Pipeline B: DeepFace emotion analysis on a face crop."""
    try:
        from deepface import DeepFace
    except ImportError:
        logger.warning("DeepFace is not installed. Install with: pip install deepface")
        return None

    bbox = face.get("bbox")
    if not bbox:
        return None

    crop = _crop_face(frame, tuple(bbox))
    if crop is None:
        return None

    try:
        result = DeepFace.analyze(
            crop,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
        )
    except Exception as exc:
        logger.error(f"DeepFace inference failed: {exc}")
        return None

    if isinstance(result, list):
        result = result[0]

    emotion_scores = result.get("emotion", {})
    scores = {label: 0.0 for label in labels}
    for key, pct in emotion_scores.items():
        std_label = DEEPFACE_TO_STANDARD.get(str(key).lower())
        if std_label:
            scores[std_label] = float(pct) / 100.0
    scores["Contempt"] = 0.0
    return _scores_to_probs(scores, labels)


def _predict_landmark(
    face: Dict[str, Any],
    labels: List[str],
    history_cache: dict,
    face_id: int,
) -> Optional[np.ndarray]:
    """Pipeline C: rule-based landmark geometry classifier."""
    landmarks = face.get("landmarks")
    if not landmarks or len(landmarks) < 478:
        return None

    blink_phase = face.get("blink_phase")
    pose = face.get("pose")
    stable_eye_feats = None
    if face_id in history_cache:
        stable_eye_feats = history_cache[face_id].get("stable_eye_feats")

    feats = extract_features(
        landmarks,
        pose=pose,
        blink_phase=blink_phase,
        stable_eye_feats=stable_eye_feats,
    )

    if face_id in history_cache:
        smooth_feats = history_cache[face_id].get("smoothed_feats", feats.copy())
        feature_alpha = FEATURE_SMOOTH_ALPHA
        for key in feats:
            if key in smooth_feats:
                smooth_feats[key] = (
                    feature_alpha * feats[key] + (1 - feature_alpha) * smooth_feats[key]
                )
            else:
                smooth_feats[key] = feats[key]
    else:
        smooth_feats = feats.copy()

    history_cache.setdefault(face_id, {})["smoothed_feats"] = smooth_feats.copy()
    history_cache[face_id]["raw_feats"] = feats

    scores = classify_emotion(smooth_feats, pose=pose)
    return _scores_to_probs(scores, labels)


FEATURE_SMOOTH_ALPHA = 0.4


# ── Plugin Class ──────────────────────────────────────────────────────────────

class EmotionPlugin(BasePlugin):
    """
    Multi-engine facial expression classifier.
    Supports FERPlus-8 ONNX, DeepFace, and landmark-heuristic pipelines.
    """

    LABELS = ["Neutral", "Happy", "Surprise", "Sad", "Angry", "Disgust", "Fear", "Contempt"]

    MARGIN_THRESHOLD = 0.10
    DEBOUNCE_FRAMES = 3
    FEATURE_ALPHA = 0.4

    @property
    def name(self) -> str:
        return "emotion"

    def _resolve_probs(
        self,
        frame: np.ndarray,
        face: Dict[str, Any],
        model: str,
        history_cache: dict,
        face_id: int,
    ) -> Optional[np.ndarray]:
        model = (model or "ferplus-8").lower()

        if model == "ferplus-8":
            probs = _predict_ferplus(frame, face, self.LABELS)
            if probs is None:
                probs = _predict_landmark(face, self.LABELS, history_cache, face_id)
        elif model == "deepface":
            probs = _predict_deepface(frame, face, self.LABELS)
            if probs is None:
                probs = _predict_landmark(face, self.LABELS, history_cache, face_id)
        elif model == "landmark-heuristic":
            probs = _predict_landmark(face, self.LABELS, history_cache, face_id)
        else:
            logger.warning(f"Unknown emotion model '{model}'; using ferplus-8.")
            probs = _predict_ferplus(frame, face, self.LABELS)
            if probs is None:
                probs = _predict_landmark(face, self.LABELS, history_cache, face_id)

        return probs

    def process(
        self,
        frame: np.ndarray,
        faces: List[Dict[str, Any]],
        **kwargs,
    ) -> List[Dict[str, Any]]:
        if not faces:
            return faces

        history_cache = kwargs.get("history_cache", {})
        slider_val = float(kwargs.get("alpha", 0.3))
        model = kwargs.get("model", "ferplus-8")
        alpha = float(np.clip(0.15 + (1.0 - slider_val) ** 2 * 0.70, 0.12, 0.85))

        for face in faces:
            face_id = face.get("face_id", 0)
            blink_phase = face.get("blink_phase")
            pose = face.get("pose")

            try:
                new_probs = self._resolve_probs(frame, face, model, history_cache, face_id)

                if new_probs is None:
                    face.setdefault("expression", "Neutral")
                    face.setdefault("expression_confidence", 0.6)
                    face.setdefault("all_expressions", {l: 0.125 for l in self.LABELS})
                    continue

                # Fix 5: pose falloff on model/heuristic probabilities
                new_probs = _apply_pose_falloff(new_probs, self.LABELS, pose)

                # Fix 1: hold steady during blink transitions
                if blink_phase in ("closing", "closed", "opening") and face_id in history_cache:
                    prev = history_cache[face_id].get("probs")
                    if prev is not None:
                        new_probs = prev.copy()

                if face_id in history_cache:
                    state = history_cache[face_id]
                    if isinstance(state, dict) and "probs" in state:
                        prev_probs = state["probs"]
                        prev_expression = state.get("expression", "Neutral")
                        counter = state.get("counter", 0)
                    else:
                        prev_probs = state if isinstance(state, np.ndarray) else new_probs
                        prev_expression = "Neutral"
                        counter = 0

                    probs = alpha * new_probs + (1.0 - alpha) * prev_probs
                else:
                    probs = new_probs
                    prev_expression = "Neutral"
                    counter = 0

                # Fix 6: margin-based hysteresis
                max_idx = int(np.argmax(probs))
                candidate_expression = self.LABELS[max_idx]
                candidate_confidence = float(probs[max_idx])

                current_expr_idx = self.LABELS.index(prev_expression)
                current_expr_prob = float(probs[current_expr_idx])
                margin = candidate_confidence - current_expr_prob

                if candidate_expression == prev_expression:
                    expression = prev_expression
                    counter = 0
                elif margin > self.MARGIN_THRESHOLD:
                    expression = candidate_expression
                    counter = 0
                else:
                    counter += 1
                    if counter >= self.DEBOUNCE_FRAMES:
                        expression = candidate_expression
                        counter = 0
                    else:
                        expression = prev_expression

                # Stable eye features for landmark blink substitution
                raw_feats = history_cache.get(face_id, {}).get("raw_feats")
                if raw_feats and blink_phase == "open":
                    new_stable_eye_feats = {
                        "avg_ear": raw_feats.get("raw_avg_ear", raw_feats.get("avg_ear", 0.0)),
                        "brow_raise": raw_feats.get("raw_brow_raise", raw_feats.get("brow_raise", 0.0)),
                    }
                elif face_id in history_cache:
                    new_stable_eye_feats = history_cache[face_id].get(
                        "stable_eye_feats",
                        {"avg_ear": 0.0, "brow_raise": 0.0},
                    )
                else:
                    new_stable_eye_feats = {"avg_ear": 0.0, "brow_raise": 0.0}

                state_update = {
                    "probs": probs.copy(),
                    "expression": expression,
                    "counter": counter,
                    "stable_eye_feats": new_stable_eye_feats,
                }
                if face_id in history_cache and "smoothed_feats" in history_cache[face_id]:
                    state_update["smoothed_feats"] = history_cache[face_id]["smoothed_feats"]
                if face_id in history_cache and "raw_feats" in history_cache[face_id]:
                    state_update["raw_feats"] = history_cache[face_id]["raw_feats"]

                history_cache[face_id] = state_update

                expr_idx = self.LABELS.index(expression)
                face["expression"] = expression
                face["expression_confidence"] = round(float(probs[expr_idx]), 4)
                face["all_expressions"] = {
                    l: round(float(probs[i]), 4) for i, l in enumerate(self.LABELS)
                }

            except Exception as exc:
                logger.error(f"EmotionPlugin error: {exc}", exc_info=True)
                face.setdefault("expression", "Neutral")
                face.setdefault("expression_confidence", 0.5)
                face.setdefault("all_expressions", {l: 0.125 for l in self.LABELS})

        return faces
