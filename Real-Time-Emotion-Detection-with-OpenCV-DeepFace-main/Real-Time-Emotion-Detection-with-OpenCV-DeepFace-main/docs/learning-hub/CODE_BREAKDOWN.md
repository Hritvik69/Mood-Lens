# 💻 The Code Breakdown (No Jargon)

So you opened `main.py` and `src/` and felt overwhelmed? Chill. It's actually super organized. Here's the map. 🗺️

## 📂 The Structure
We didn't just dump everything in one file (spaghetti code 🍝). We split it up:

- **`main.py`**: The Boss. It tells everyone else what to do.
- **`src/core/`**: The Brains. Camera, AI, Face Detection.
- **`src/ui/`**: The Looks. Drawing the bars, text, and cool colors.
- **`src/utils/`**: The Helpers. FPS counter, logger.

## 🕵️‍♂️ Deep Dive: `main.py`

This is the loop that runs forever (until you press Q).

```python
while True:
    # 1. Get the picture
    frame = camera.read()
    
    # 2. Find the face
    face = detect_face(frame)
    
    # 3. Ask the AI "What emotion is this?"
    # (We only do this every few frames to keep it fast!)
    if frame_count % 3 == 0:
        emotion = analyzer.analyze(face)
        
    # 4. Draw the cool graphics
    visualizer.draw_hud(frame, emotion)
    
    # 5. Show it on screen
    cv2.imshow("Window", frame)
```

## 🧠 The Analyzer (`src/core/analyzer.py`)
This is where the magic happens.
- It loads the **DeepFace** model or our custom model.
- It runs the prediction in a **separate thread**. Why? So the video doesn't freeze while the AI is thinking!

## 🎥 The Camera (`src/core/camera.py`)
OpenCV's default camera reading is kinda slow.
We made a **Threaded Camera**.
- One worker thread does nothing but grab frames as fast as possible.
- The main thread just asks "Give me the latest frame".
- Result: **Butter smooth video.** 🧈

## 🎨 The Visualizer (`src/ui/visualizer.py`)
This file is just an artist.
- It takes the emotion data.
- It calculates how long the bars should be.
- It picks the colors (Yellow for Happy, Blue for Sad).
- It draws rectangles and text on the image.

---

## 💡 Pro Tip
If you want to change how the app *looks*, go to `src/ui/visualizer.py`.
If you want to change how the app *thinks*, go to `src/core/analyzer.py`.

👉 **Next: [Speed Hacks](PERFORMANCE_HACKS.md)**
