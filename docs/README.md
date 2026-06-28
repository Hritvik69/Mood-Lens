# EmotionVision AI

EmotionVision AI is an enterprise-grade, local-first web application for real-time facial feature tracking and classification of facial expressions.

```
                  ┌─────────────────────────────────────────┐
                  │          React Frontend Client          │
                  │   - Web Worker thread captures frames   │
                  │   - Renders 60 FPS CSS & mesh overlays │
                  └────────────────────┬────────────────────┘
                                       │ (Binary WebSockets)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │           FastAPI Python API            │
                  │   - Centroid-based multiple face ID    │
                  │   - Head Pose and Aspect Ratio metrics  │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    Landmark-Geometry Classifier        │
                  │   - MediaPipe 478-point Face Mesh       │
                  │   - Real-time geometric feature analysis │
                  │   - No external ONNX model required      │
                  └─────────────────────────────────────────┘
```

## Key Capabilities

1. **Facial Expression Classification**: Real-time classification using landmark geometry from MediaPipe Face Mesh. Detects: *Neutral, Happy, Surprise, Sad, Angry, Disgust, Fear, Contempt*.
2. **Custom Vision Analytics**:
   - **Blink Rate & Fatigue Analysis**: Tracks Eye Aspect Ratios (EAR) and triggers alarms for drowsiness (eyes closed > 1.5s).
   - **Eye Contact Indicator**: Measures iris offsets relative to eye boundaries.
   - **Smile & Mouth Intensity**: Computes normalized ratios of mouth dimensions.
3. **Spatial & Environment Diagnostics**:
   - **3D Head Pose Estimator**: Solves rotation matrices (Pitch, Yaw, Roll) via PnP.
   - **Centering & Distance**: Measures offset from loop center and approximate distance in meters.
   - **Lighting Assessment**: Computes luminance mean and contrast thresholds.
4. **Performance & Security Features**:
   - **Web Worker Isolated Threading**: Image JPEG compression and sockets communications are offloaded from the UI main thread.
   - **DuckDB Aggregate Dashboards**: Speeds up statistics rendering by querying database files directly.
   - **Zero Cloud Leakage**: All streams are processed in-memory locally.

## Technology Stack

* **Frontend Client**: React 19, TypeScript, Vite, Tailwind CSS, Framer Motion, Recharts, Lucide Icons.
* **Backend Server**: FastAPI, Python 3, OpenCV, MediaPipe Face Mesh.
* **Storage Engine**: SQLite (Transactional logs) + DuckDB (Analytical queries).
