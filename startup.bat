@echo off
title EmotionVision AI Startup Manager
echo ========================================================
echo          EmotionVision AI - Startup Manager
echo ========================================================
echo.

:: Check for python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.9+ and try again.
    pause
    exit /b 1
)

:: Check for node installation
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH. Please install Node.js and try again.
    pause
    exit /b 1
)

:: 1. Backend Setup
echo [SYSTEM] Configuring Python Backend...
cd backend
if not exist venv (
    echo [SYSTEM] Creating virtual environment venv...
    python -m venv venv
)

echo [SYSTEM] Activating venv and updating packages...
call venv\Scripts\activate
python -m pip install --upgrade pip
echo [SYSTEM] Installing Python dependencies...
pip install -r requirements.txt

echo [SYSTEM] Launching FastAPI backend server in a separate window...
start "EmotionVision AI - Backend API" cmd /k "call venv\Scripts\activate && python -m uvicorn main:app --host 127.0.0.1 --port 8000"
cd ..

:: 2. Frontend Setup
echo [SYSTEM] Configuring React Frontend...
cd frontend
echo [SYSTEM] Launching Vite development server in a separate window...
start "EmotionVision AI - Frontend Client" cmd /k "npm run dev"
cd ..

echo.
echo ========================================================
echo          SERVERS INITIATED SUCCESSFULLY!
echo.
echo  * Backend API:  http://127.0.0.1:8000
echo  * Frontend:     http://localhost:5173
echo.
echo Opening default web browser...
echo ========================================================
echo.

timeout /t 5 >nul
start http://localhost:5173
pause
