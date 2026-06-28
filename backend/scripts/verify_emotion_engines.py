"""
Verification script for MoodLens emotion detection pipelines.

Usage (from backend/):
    python scripts/verify_emotion_engines.py

Checks FERPlus-8 ONNX inference, landmark heuristics, and optionally DeepFace
on a synthetic face crop.
"""

import sys
from pathlib import Path

import cv2
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from plugins.emotion import (  # noqa: E402
    EmotionPlugin,
    _predict_ferplus,
    _predict_deepface,
    _predict_landmark,
    _softmax,
)
from services.model_manager import model_manager  # noqa: E402


def make_dummy_frame() -> np.ndarray:
    """Solid gray frame with a centered pseudo-face region."""
    frame = np.full((480, 640, 3), 128, dtype=np.uint8)
    cv2.rectangle(frame, (220, 120), (420, 360), (200, 180, 160), -1)
    return frame


def make_dummy_face() -> dict:
    return {
        "face_id": 1,
        "bbox": (220.0, 120.0, 200.0, 240.0),
        "landmarks": [[0.5, 0.5, 0.0] for _ in range(478)],
        "pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
    }


def verify_softmax():
    logits = np.array([1.0, 2.0, 0.5, -1.0, 0.0, 0.0, 0.0, 0.0])
    probs = _softmax(logits)
    assert abs(probs.sum() - 1.0) < 1e-6, "Softmax probabilities must sum to 1"
    print("[OK] Softmax normalization")


def verify_ferplus(frame, face, labels):
    try:
        model_manager.load_model()
    except Exception as exc:
        print(f"[SKIP] FERPlus-8: model load failed ({exc})")
        return

    probs = _predict_ferplus(frame, face, labels)
    if probs is None:
        print("[FAIL] FERPlus-8 returned None")
        return

    assert len(probs) == 8, f"Expected 8 outputs, got {len(probs)}"
    assert abs(probs.sum() - 1.0) < 1e-4, "FERPlus probs must sum to ~1 after softmax"
    top = labels[int(np.argmax(probs))]
    print(f"[OK] FERPlus-8 inference — top emotion: {top} ({probs.max():.3f})")


def verify_landmark(face, labels):
    history = {}
    probs = _predict_landmark(face, labels, history, face_id=1)
    if probs is None:
        print("[FAIL] Landmark heuristic returned None")
        return

    assert len(probs) == 8
    assert abs(probs.sum() - 1.0) < 1e-4
    top = labels[int(np.argmax(probs))]
    print(f"[OK] Landmark heuristic — top emotion: {top} ({probs.max():.3f})")


def verify_deepface(frame, face, labels):
    try:
        import deepface  # noqa: F401
    except ImportError:
        print("[SKIP] DeepFace: not installed (pip install deepface)")
        return

    probs = _predict_deepface(frame, face, labels)
    if probs is None:
        print("[FAIL] DeepFace returned None")
        return

    assert len(probs) == 8
    assert abs(probs.sum() - 1.0) < 1e-4
    top = labels[int(np.argmax(probs))]
    print(f"[OK] DeepFace inference — top emotion: {top} ({probs.max():.3f})")


def verify_plugin_integration(frame, face):
    plugin = EmotionPlugin()
    history = {}

    for model in ("ferplus-8", "landmark-heuristic", "deepface"):
        faces = [dict(face)]
        result = plugin.process(frame, faces, history_cache=history, alpha=0.3, model=model)
        expr = result[0].get("expression", "Unknown")
        conf = result[0].get("expression_confidence", 0.0)
        print(f"[OK] EmotionPlugin model={model} — {expr} ({conf:.3f})")


def main():
    print("MoodLens Emotion Engine Verification")
    print("=" * 40)

    labels = EmotionPlugin.LABELS
    frame = make_dummy_frame()
    face = make_dummy_face()

    verify_softmax()
    verify_ferplus(frame, face, labels)
    verify_landmark(face, labels)
    verify_deepface(frame, face, labels)
    verify_plugin_integration(frame, face)

    print("=" * 40)
    print("Verification complete.")


if __name__ == "__main__":
    main()
