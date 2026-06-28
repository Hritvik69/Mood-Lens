# Mood-Lens

Real-time facial expression detection web app with multiple AI engines: FERPlus-8 (ONNX), DeepFace, and landmark heuristics.

## Quick start

1. Run `startup.bat` (Windows) to start the backend and frontend.
2. Open the app in your browser and start the live camera stream.
3. Choose an emotion engine in **Settings** (FERPlus-8 is the default).

## Project structure

- `backend/` — FastAPI WebSocket API, MediaPipe face mesh, emotion plugins
- `frontend/` — React + Vite client with live camera UI
- `docs/` — Installation and architecture docs
- `models/` — ONNX model downloaded automatically on first run

## Emotion engines

| Engine | Speed | Notes |
|--------|-------|-------|
| `ferplus-8` | ~10 ms | Default; ONNX Runtime |
| `deepface` | ~200–500 ms | Optional; `pip install deepface` |
| `landmark-heuristic` | Fast | Rule-based geometry |

See [docs/installation.md](docs/installation.md) for full setup instructions.
