# 🚀 Quick Start Guide

Get up and running in 5 minutes!

## 1️⃣ Install Python

Download and install Python 3.8+ from [python.org](https://www.python.org/downloads/)

**Windows users**: Make sure to check "Add Python to PATH" during installation!

## 2️⃣ Clone or Download

```bash
git clone https://github.com/Shayanthn/Real-Time-Emotion-Detection-with-OpenCV-DeepFace.git
cd Real-Time-Emotion-Detection-with-OpenCV-DeepFace
```

Or download and extract the ZIP file.

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This may take a few minutes. Grab a coffee! ☕

## 4️⃣ Run the Application

```bash
python main.py
```

## 🎮 Controls

- Press `Q` to quit
- Press `R` to start/stop recording

## ⚠️ Troubleshooting

### Camera not working?
Make sure no other application is using your camera.

### Import errors?
Try reinstalling:
```bash
pip install --upgrade --force-reinstall -r requirements.txt
```

### Low FPS?
Edit `src/config.py` and increase `ANALYSIS_THROTTLE` to 5 or higher.

---

**Need more help?** Check [INSTALLATION.md](INSTALLATION.md) for detailed instructions.

<p align="center">
  Made with ❤️ by <a href="https://shayantaherkhani.ir">Shayan Taherkhani</a>
</p>
