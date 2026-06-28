import os

class Config:
    # Window Settings
    WINDOW_NAME = "Advanced Emotion Analytics"
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60
    
    # Camera Settings
    CAMERA_ID = 0
    CAMERA_WIDTH = 1920
    CAMERA_HEIGHT = 1080
    
    # Model Settings
    # Path to the pre-trained model if available
    MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fer2013_mini_XCEPTION.102-0.66.hdf5')
    USE_DEEPFACE = True
    USE_CUSTOM_MODEL = True
    
    # Performance Settings
    ANALYSIS_THROTTLE = 3  # Analyze every N frames to improve performance
    
    # Analysis Settings
    ANALYSIS_INTERVAL = 0.1  # Seconds between emotion checks
    SMOOTHING_WINDOW = 10    # For emotion history
    
    # Visualization
    SHOW_FPS = True
    SHOW_GRAPH = True
    THEME_COLOR = (0, 255, 255) # Cyan
    
    # Developer Info
    DEV_NAME = "Shayan Taherkhani"
    DEV_WEBSITE = "shayantaherkhani.ir"
    
    # Emotions
    EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
    EMOTION_COLORS = {
        "happy": (0, 255, 255),    # Yellow/Cyan mix
        "sad": (255, 50, 50),      # Blue-ish
        "angry": (0, 0, 255),      # Red
        "surprise": (255, 0, 255), # Magenta
        "fear": (0, 165, 255),     # Orange
        "disgust": (0, 255, 0),    # Green
        "neutral": (200, 200, 200) # Gray
    }
