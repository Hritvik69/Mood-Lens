# Emotion Classification: Landmark-Geometry Approach

This document details the emotion classification approach used by **EmotionVision AI** — a geometric, rule-based system using MediaPipe Face Mesh landmarks instead of a neural network.

---

## 1. Overview

The system uses **MediaPipe Face Mesh** to detect 478 facial landmarks per face, then applies geometric feature analysis to classify emotions. This approach is:
- **Real-time**: No heavy inference needed
- **Interpretable**: Clear rules for each emotion
- **Calibratable**: Thresholds can be tuned per camera/face

---

## 2. Geometric Features

All features are **scale-invariant**, normalized by inter-ocular distance (IOD).

| Feature | Formula | Description |
|---------|---------|-------------|
| `corner_below_lip` | `(mouth_corner_y - upper_lip_y) / IOD` | Positive = corners below lip = smile |
| `mouth_open_ratio` | `mouth_height / mouth_width` | Higher = more open mouth |
| `avg_ear` | Eye vertical / Eye horizontal | Eye Aspect Ratio |
| `brow_raise` | `(eye_top_y - brow_y) / IOD` | Positive = brows above eyes |
| `brow_furrow` | `|left_brow_x - right_brow_x| / IOD` | Smaller = more furrowed |
| `nose_to_lip` | `distance(nose_tip, upper_lip) / IOD` | Smaller = nose wrinkled (disgust) |
| `corner_asym` | `|left_corner_y - right_corner_y| / IOD` | Larger = asymmetric (contempt) |

---

## 3. Emotion Classification Rules

Emotions are classified using **sigmoid-based scoring functions**. Each emotion requires specific feature combinations:

| Emotion | Primary Features | Secondary Features |
|---------|----------------|-------------------|
| **Happy** | `corner_below_lip > 0.10` | `mouth_open_ratio > 0.25` |
| **Sad** | `corner_below_lip > 0.10` | `mouth_open_ratio < 0.18` (nearly closed) |
| **Angry** | `brow_furrow < 0.25` | `mouth_open_ratio < 0.14` (tight lips) |
| **Surprise** | `mouth_open_ratio > 0.60` | - |
| **Fear** | `avg_ear > 0.30` | `mouth_open_ratio < 0.30` |
| **Disgust** | `nose_to_lip < 0.10` | `mouth_open_ratio < 0.30` |
| **Contempt** | `corner_asym > 0.15` | - |
| **Neutral** | Inverse of max(other emotions) | - |

---

## 4. Feature Smoothing & Stability

### Feature-Level EMA
Before classification, raw geometric features are smoothed using Exponential Moving Average:
```
smoothed[key] = α_feat * new_value + (1 - α_feat) * prev_value
```
Where `α_feat = 0.4` (40% new, 60% previous).

### Probability-Level EMA
After classification, probabilities are smoothed to prevent flickering:
```
probs = α_prob * new_probs + (1 - α_prob) * prev_probs
```
Where `α_prob` ranges from 0.12 to 0.85 based on UI slider.

### Margin-Based Hysteresis
Emotion switches require:
1. New candidate beats current by margin > 0.10
2. AND 3 consecutive frames of same candidate

---

## 5. Blink Coupling

During eye blinks, the `BlinkPlugin` exposes a `blink_phase`:
- `"open"`: Normal open eyes
- `"closing"`: Transitioning to closed
- `"closed"`: Eyes fully closed
- `"opening"`: 1-2 frames after reopening (suppresses spring-open overshoot)

During `closing`/`closed`/`opening` phases, eye-based features (`avg_ear`, `brow_raise`) use **stable pre-blink values** to prevent blink transients from triggering Fear/Surprise.

---

## 6. Head Pose Compensation

When head pitch > 15° or yaw > 20°, confidence for pose-sensitive emotions (Fear, Surprise, Sad) is reduced by a falloff factor:
```
falloff = max(0.3, 1 - (pitch-15)/60 - (yaw-20)/80)
```

---

## 7. Output

The system outputs:
- `expression`: Top emotion label
- `expression_confidence`: Probability of top emotion (0-1)
- `all_expressions`: Dict of all 8 emotions with probabilities

Emotion labels (in order):
```
0: Neutral, 1: Happy, 2: Surprise, 3: Sad, 
4: Angry, 5: Disgust, 6: Fear, 7: Contempt
```
