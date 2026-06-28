# API & WebSockets Contract Specification

This document details the REST API endpoints and real-time WebSocket protocol contracts for **EmotionVision AI**.

---

## 1. REST HTTP Endpoints

All endpoints are hosted by default on `http://127.0.0.1:8000`.

### Health Check
* **Endpoint**: `/api/health`
* **Method**: `GET`
* **Response**:
  ```json
  {
    "status": "healthy",
    "app_name": "EmotionVision AI",
    "model_loaded": true,
    "execution_provider": "CPUExecutionProvider"
  }
  ```

### Paginated History Logs
* **Endpoint**: `/api/history`
* **Method**: `GET`
* **Query Parameters**:
  * `page` (int, default=1): Page index.
  * `limit` (int, default=50): Records per page.
  * `session_id` (string, optional): Filter by session.
  * `expression` (string, optional): Filter by expression class.

### CSV & JSON Exports
* **Endpoints**:
  * `/api/history/export/csv` (`GET`): Downloads a CSV file.
  * `/api/history/export/json` (`GET`): Downloads a JSON file.

### DuckDB Summary Analytics
* **Endpoint**: `/api/analytics/summary`
* **Method**: `GET`
* **Response**:
  ```json
  {
    "total_detections": 1240,
    "total_sessions": 3,
    "average_confidence": 78.43,
    "average_inference_ms": 12.4,
    "average_quality": 84.5,
    "drowsiness_alerts": 2
  }
  ```

---

## 2. WebSocket Protocol (`/ws`)

The WebSocket endpoint manages high-frequency streaming packets.

### Client-to-Server Messages
1. **Config Packet (Text JSON)**: Sent during initialization or when sliders are adjusted.
   ```json
   {
     "session_id": "sess_1719515000",
     "confidence_threshold": 0.50,
     "confidence_smoothing": 0.30,
     "record_history": true
   }
   ```
2. **Video Frame (Binary ArrayBuffer)**: Raw binary bytes of compressed JPEG frames captured from the webcam.

### Server-to-Client Responses (JSON)
Pushed back immediately after each frame is processed:
```json
{
  "session_id": "sess_1719515000",
  "faces": [
    {
      "face_id": 1,
      "bbox": [120.5, 80.0, 320.0, 320.0],
      "landmarks": [[0.5211, 0.3122, -0.012], "..."],
      "pose": { "pitch": 4.5, "yaw": -2.1, "roll": 0.5 },
      "distance": 0.82,
      "quality": {
        "score": 82.5,
        "lighting": 90.0,
        "blur": 85.0,
        "centering": 75.0,
        "recommendations": ["Face quality optimal"]
      },
      "expression": "Happy",
      "expression_confidence": 0.924,
      "all_expressions": {
        "Neutral": 0.05,
        "Happy": 0.924,
        "Surprise": 0.01,
        "Sad": 0.01,
        "Angry": 0.003,
        "Disgust": 0.001,
        "Fear": 0.001,
        "Contempt": 0.001
      },
      "blink_metrics": {
        "ear": 0.28,
        "blink_rate": 12,
        "drowsiness_detected": false,
        "eye_contact": true,
        "smile_intensity": 84.2,
        "mouth_openness": 5.4
      }
    }
  ],
  "performance": {
    "total_latency_ms": 18.5,
    "mediapipe_latency_ms": 10.2,
    "plugins_latency_ms": 8.3,
    "inference_latency_ms": 8.3,
    "fps": 29.8
  },
  "system": {
    "cpu_usage": 14.5,
    "ram_usage": 42.1,
    "gpu_engine": "CPUExecutionProvider",
    "fps": 29.8
  }
}
```
