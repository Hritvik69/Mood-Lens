# Installation & Setup Guide

This guide details the steps required to configure and run the **EmotionVision AI** application on a local development environment.

## 1. Prerequisites

Ensure your system has the following installed:
* **Python**: Version 3.9 to 3.12 (Python 3.13 might have compatibility issues with pre-built MediaPipe wheels).
* **Node.js**: Version 18.0 or newer.
* **Webcam**: A functional USB or integrated camera.

---

## 2. Fast Launch (Windows)

A single-click startup script is provided at the root of the project:

1. Double-click the `startup.bat` file in the root workspace folder.
2. The script will automatically:
   * Build the Python virtual environment (`backend/venv`).
   * Install/update python libraries via `pip install -r requirements.txt`.
   * Pre-download the pre-trained `emotion-ferplus-8.onnx` model (if missing).
   * Launch the FastAPI backend on `http://127.0.0.1:8000`.
   * Start the Vite React client on `http://localhost:5173`.
   * Open the client in your default web browser.

---

## 3. Manual Installation

If you prefer to run steps manually, or are deploying on macOS/Linux:

### Step A: Configure and Start the Backend
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Windows
   python -m venv venv
   source venv/Scripts/activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install package dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server using Uvicorn:
   ```bash
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

### Step B: Configure and Start the Frontend
1. Open a second terminal window and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to `http://localhost:5173`.

---

## 4. Troubleshooting Diagnostics

* **Camera Permission Blocked**: Ensure that you have granted permission in your web browser. Chrome will show a small video icon in the URL search bar if permissions are blocked.
* **Port Conflict (8000/5173 already occupied)**: If port 8000 is occupied, you can edit `backend/core/config.py` to change the default port, and update the websocket URL in `frontend/src/pages/LiveCamera.tsx` accordingly.
* **ONNX model download failure**: If your company firewall blocks model downloading, manually download `emotion-ferplus-8.onnx` from Hugging Face and place it inside the root `models/` directory before starting the application.
