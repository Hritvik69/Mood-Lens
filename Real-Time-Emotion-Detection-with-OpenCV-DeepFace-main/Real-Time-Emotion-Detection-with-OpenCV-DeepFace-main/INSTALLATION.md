# 🚀 Installation & Setup Guide

Complete guide for setting up the Real-Time Emotion Detection system.

---

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux (Ubuntu 18.04+), or macOS 10.14+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum
- **Camera**: Built-in webcam or USB camera
- **Processor**: Intel Core i5 or equivalent

### Recommended Requirements
- **RAM**: 8GB or more
- **GPU**: NVIDIA GPU with CUDA support (for faster processing)
- **Processor**: Intel Core i7 or AMD Ryzen 5 or higher

---

## ⚙️ Installation Steps

### 1. Install Python

If Python is not installed on your system:

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. ✅ **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```powershell
   python --version
   ```

#### Linux
```bash
sudo apt update
sudo apt install python3 python3-pip
python3 --version
```

#### macOS
```bash
# Using Homebrew
brew install python3
python3 --version
```

---

### 2. Clone the Repository

```bash
git clone https://github.com/Shayanthn/Real-Time-Emotion-Detection-with-OpenCV-DeepFace.git
cd Real-Time-Emotion-Detection-with-OpenCV-DeepFace
```

Or download the ZIP file from GitHub and extract it.

---

### 3. Create Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated.

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal after activation.

---

### 4. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This will install:
- opencv-python
- mediapipe
- deepface
- tensorflow
- pygame
- scipy
- numpy
- kaggle

**Note**: Installation may take 5-10 minutes depending on your internet speed.

---

### 5. Download Pre-trained Model (Optional but Recommended)

The system works with DeepFace out of the box, but for better performance:

1. Download the FER2013 Mini-XCEPTION model:
   - Direct link: [fer2013_mini_XCEPTION.102-0.66.hdf5](https://github.com/oarriaga/face_classification/blob/master/trained_models/emotion_models/fer2013_mini_XCEPTION.102-0.66.hdf5)
   
2. Place the downloaded file in the project root directory

---

### 6. Setup Kaggle (Optional - For Dataset Download)

Only needed if you want to download the FER2013 dataset for training/experiments.

1. Create Kaggle account at [kaggle.com](https://www.kaggle.com/)
2. Go to Account Settings → API → "Create New API Token"
3. Download `kaggle.json`
4. Place it in the correct location:
   - **Windows**: `C:\Users\<YourUsername>\.kaggle\kaggle.json`
   - **Linux/macOS**: `~/.kaggle/kaggle.json`

5. Download the dataset:
   ```bash
   python scripts/download_dataset.py
   ```

For detailed instructions, see [KAGGLE_SETUP.md](KAGGLE_SETUP.md).

---

## ▶️ Running the Application

### Basic Run

```bash
python main.py
```

### Expected Output

You should see:
```
🚀 Starting Advanced Emotion Analytics System...
✅ Custom FER Model Loaded.
✅ System Ready. Press 'q' to exit, 'r' to toggle recording.
```

A window will open showing your camera feed with emotion detection overlay.

---

## 🎮 Controls

While the application is running:

| Key | Function |
|-----|----------|
| `Q` | Quit the application |
| `R` | Start/Stop recording video |

---

## 🐛 Troubleshooting

### Issue: "No module named 'cv2'"
**Solution**: Reinstall OpenCV
```bash
pip uninstall opencv-python
pip install opencv-python
```

### Issue: Camera not detected
**Solution**: 
1. Check if camera is working in other apps
2. Try changing `CAMERA_ID` in `src/config.py`:
   ```python
   CAMERA_ID = 1  # Try 0, 1, 2
   ```

### Issue: "Could not load custom model"
**Solution**: This is normal if you haven't downloaded the model. The system will use DeepFace automatically.

### Issue: Low FPS / Laggy performance
**Solutions**:
1. Reduce camera resolution in `src/config.py`:
   ```python
   CAMERA_WIDTH = 1280
   CAMERA_HEIGHT = 720
   ```
2. Increase throttle value:
   ```python
   ANALYSIS_THROTTLE = 5  # Analyze every 5 frames instead of 3
   ```

### Issue: "ImportError: DLL load failed" (Windows)
**Solution**: Install Visual C++ Redistributables
- Download from [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Issue: TensorFlow warnings
**Solution**: These are normal and can be ignored. To suppress:
```python
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
```
(Already included in the code)

---

## 🔧 Advanced Configuration

Edit `src/config.py` to customize:

### Camera Settings
```python
CAMERA_WIDTH = 1920       # Resolution width
CAMERA_HEIGHT = 1080      # Resolution height
FPS = 60                  # Target FPS
```

### Performance Settings
```python
ANALYSIS_THROTTLE = 3     # Analyze every N frames (higher = faster but less responsive)
ANALYSIS_INTERVAL = 0.1   # Minimum time between analyses (seconds)
```

### Visual Settings
```python
SHOW_FPS = True          # Display FPS counter
SHOW_GRAPH = True        # Show emotion history graph
THEME_COLOR = (0, 255, 255)  # UI accent color (BGR)
```

---

## 📦 GPU Acceleration (Optional)

For NVIDIA GPU users to enable CUDA acceleration:

1. Install CUDA Toolkit (11.2+)
2. Install cuDNN
3. Install GPU-enabled TensorFlow:
   ```bash
   pip uninstall tensorflow
   pip install tensorflow-gpu
   ```

Verify GPU is detected:
```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))
```

---

## 🧪 Testing the Installation

Run a quick test:

```bash
python -c "import cv2, tensorflow, deepface, mediapipe; print('✅ All imports successful!')"
```

If this prints `✅ All imports successful!`, you're ready to go!

---

## 📞 Getting Help

If you encounter issues:

1. Check [Troubleshooting](#-troubleshooting) section above
2. Search existing [Issues](https://github.com/Shayanthn/Real-Time-Emotion-Detection-with-OpenCV-DeepFace/issues)
3. Create a new issue with:
   - Your OS and Python version
   - Full error message
   - Steps to reproduce

---

## 🔄 Updating the Project

To get the latest version:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

<p align="center">
  Made with ❤️ by <a href="https://shayantaherkhani.ir">Shayan Taherkhani</a>
</p>
