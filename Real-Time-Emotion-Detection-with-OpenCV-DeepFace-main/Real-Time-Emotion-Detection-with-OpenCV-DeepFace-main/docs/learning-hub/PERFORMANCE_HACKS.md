# ⚡ Performance Hacks (How we got 60 FPS)

You might notice other Python AI projects run at like 5 FPS (laggy mess). Ours runs at 60+. How? 🤔

Here are the secrets. Steal these for your own projects.

## 1. Multithreading is Key 🧵
Python is usually single-threaded (does one thing at a time).
- **Bad way**: Read Frame -> Wait for AI -> Draw -> Show. (Video freezes while AI thinks).
- **Our way**: 
    - Thread 1: Read Camera (Always running)
    - Thread 2: AI Analysis (Runs in background)
    - Main Thread: Draw & Show (Always running)

This means the video **never stops**. Even if the AI takes 1 second to think, the video keeps playing at 60 FPS.

## 2. Frame Throttling 🛑
We don't need to check your emotion 60 times a second. Your face doesn't change that fast!
We check the emotion **every 3rd or 5th frame**.
- Frame 1: Draw old emotion
- Frame 2: Draw old emotion
- Frame 3: **Run AI** & Update emotion
- Frame 4: Draw new emotion...

This saves HUGE amounts of CPU power.

## 3. Image Resizing 📉
Processing a 1080p image is slow.
Before sending the face to the AI, we shrink it to **48x48 pixels**.
Smaller image = Faster math = Higher FPS.

## 4. Efficient Drawing 🎨
We use OpenCV's built-in drawing functions (`cv2.rectangle`, `cv2.putText`). They are written in C++ and are super fast. We avoid complex Python loops for pixel manipulation.

## 5. The "Deque" Trick
For the FPS counter, we use a `deque` (double-ended queue) to store the last 30 frame times. It's way faster than a normal list for adding/removing items constantly.

---

## 🚀 TL;DR
- Don't block the main loop.
- Don't process every single frame.
- Keep data small.

👉 **Next: [Make It Yours](MAKE_IT_YOURS.md)**
