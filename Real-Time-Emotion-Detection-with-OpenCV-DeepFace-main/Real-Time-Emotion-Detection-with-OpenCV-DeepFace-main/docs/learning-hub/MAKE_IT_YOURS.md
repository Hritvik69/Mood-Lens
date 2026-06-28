# 🎨 Make It Yours (Customization Guide)

Okay, you got it running. Now let's make it **cool**. Here is how you can mod this project.

## 1. Change the Colors 🌈
Hate the colors? Change them!
Open `src/config.py`.
Look for `EMOTION_COLORS`.

```python
EMOTION_COLORS = {
    "happy": (0, 255, 255),    # Yellow (BGR format)
    "sad": (255, 0, 0),        # Blue
    "angry": (0, 0, 255),      # Red
    # ...
}
```
*Note: OpenCV uses BGR (Blue-Green-Red), not RGB. So (255, 0, 0) is Blue, not Red!*

## 2. Add Your Own Sounds 🔊
Want it to play a sound when you smile?
1. Put a `.wav` file in the folder.
2. Open `main.py`.
3. Import `pygame` and load the sound.

```python
# At the top
import pygame
pygame.mixer.init()
happy_sound = pygame.mixer.Sound("happy.wav")

# Inside the loop, where emotion is checked
if emotion == "happy" and last_emotion != "happy":
    happy_sound.play()
```

## 3. Save the Data 📊
Want to save a log of your emotions?
Open `main.py` and add simple file writing.

```python
with open("emotions.csv", "a") as f:
    f.write(f"{time.time()},{emotion}\n")
```

## 4. Change the UI Layout 🖼️
Go to `src/ui/visualizer.py`.
The function `draw_hud` controls everything.
- Change coordinates `(x, y)` to move text around.
- Change `cv2.FONT_HERSHEY_SIMPLEX` to a different font.

---

## 🏆 Challenge
Can you make it detect when you are **"Surprised"** and automatically take a screenshot? 📸
*Hint: Check the emotion variable and use `cv2.imwrite`.*

**Good luck! Go build something awesome.** 🚀
