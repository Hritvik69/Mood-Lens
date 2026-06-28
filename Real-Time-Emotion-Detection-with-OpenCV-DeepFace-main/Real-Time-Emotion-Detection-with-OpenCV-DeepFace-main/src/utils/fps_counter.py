"""
FPS Counter utility
"""
import time
from collections import deque

class FPSCounter:
    def __init__(self, window_size=30):
        self.timestamps = deque(maxlen=window_size)
        
    def update(self):
        self.timestamps.append(time.time())
        
    def get_fps(self):
        if len(self.timestamps) < 2:
            return 0.0
        
        elapsed = self.timestamps[-1] - self.timestamps[0]
        if elapsed == 0:
            return 0.0
            
        return len(self.timestamps) / elapsed
