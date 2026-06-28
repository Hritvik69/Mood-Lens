# 📊 Working with FER2013 Dataset

This guide explains how to use the downloaded FER2013 dataset for training and evaluation.

## 📥 Dataset Overview

**FER2013** (Facial Expression Recognition 2013) is a large-scale dataset for emotion recognition:

- **Total Images**: 35,887 grayscale images
- **Resolution**: 48x48 pixels
- **Classes**: 7 emotions (angry, disgust, fear, happy, sad, surprise, neutral)
- **Splits**: Training, Validation, Test

## 📂 Dataset Structure

After downloading with `python scripts/download_dataset.py`, the structure will be:

```
data/
└── fer2013/
    ├── train/
    │   ├── angry/
    │   ├── disgust/
    │   ├── fear/
    │   ├── happy/
    │   ├── sad/
    │   ├── surprise/
    │   └── neutral/
    └── test/
        ├── angry/
        ├── disgust/
        ├── fear/
        ├── happy/
        ├── sad/
        ├── surprise/
        └── neutral/
```

## 📊 Dataset Statistics

| Emotion | Training Samples | Test Samples |
|---------|-----------------|--------------|
| Angry | ~4,000 | ~958 |
| Disgust | ~547 | ~111 |
| Fear | ~4,000 | ~1,024 |
| Happy | ~7,000 | ~1,774 |
| Sad | ~4,000 | ~1,247 |
| Surprise | ~3,000 | ~831 |
| Neutral | ~4,000 | ~1,233 |

**Note**: Disgust class is significantly underrepresented (class imbalance).

## 🔬 Using the Dataset

### Option 1: Training a New Model

Create a training script (`scripts/train_model.py`):

```python
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Dropout

# Data augmentation
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True
)

test_datagen = ImageDataGenerator(rescale=1./255)

# Load data
train_generator = train_datagen.flow_from_directory(
    'data/fer2013/train',
    target_size=(48, 48),
    color_mode='grayscale',
    batch_size=32,
    class_mode='categorical'
)

test_generator = test_datagen.flow_from_directory(
    'data/fer2013/test',
    target_size=(48, 48),
    color_mode='grayscale',
    batch_size=32,
    class_mode='categorical'
)

# Build model
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(48, 48, 1)),
    MaxPooling2D(2, 2),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(7, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Train
history = model.fit(
    train_generator,
    epochs=30,
    validation_data=test_generator
)

# Save
model.save('my_emotion_model.h5')
```

### Option 2: Evaluate Existing Model

Test your model's performance:

```python
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np

# Load model
model = load_model('fer2013_mini_XCEPTION.102-0.66.hdf5')

# Prepare test data
test_datagen = ImageDataGenerator(rescale=1./255)
test_generator = test_datagen.flow_from_directory(
    'data/fer2013/test',
    target_size=(48, 48),
    color_mode='rgb',  # or 'grayscale' depending on model
    batch_size=32,
    class_mode='categorical',
    shuffle=False
)

# Evaluate
loss, accuracy = model.evaluate(test_generator)
print(f"Test Accuracy: {accuracy*100:.2f}%")

# Predictions
predictions = model.predict(test_generator)
predicted_classes = np.argmax(predictions, axis=1)
true_classes = test_generator.classes

# Confusion matrix
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt

cm = confusion_matrix(true_classes, predicted_classes)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()

# Classification report
emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
print(classification_report(true_classes, predicted_classes, target_names=emotions))
```

### Option 3: Data Exploration

Explore the dataset:

```python
import os
import cv2
import matplotlib.pyplot as plt
import random

data_dir = 'data/fer2013/train'
emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

# Display random samples
fig, axes = plt.subplots(3, 7, figsize=(15, 8))

for i, emotion in enumerate(emotions):
    emotion_dir = os.path.join(data_dir, emotion)
    images = os.listdir(emotion_dir)
    
    for j in range(3):
        img_path = os.path.join(emotion_dir, random.choice(images))
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        
        axes[j, i].imshow(img, cmap='gray')
        axes[j, i].axis('off')
        if j == 0:
            axes[j, i].set_title(emotion.capitalize())

plt.tight_layout()
plt.show()
```

## 🔧 Handling Class Imbalance

The disgust class has very few samples. Solutions:

### 1. Class Weights

```python
from sklearn.utils import class_weight
import numpy as np

class_weights = class_weight.compute_class_weight(
    'balanced',
    classes=np.unique(train_generator.classes),
    y=train_generator.classes
)
class_weight_dict = dict(enumerate(class_weights))

model.fit(
    train_generator,
    class_weight=class_weight_dict,
    epochs=30
)
```

### 2. Oversampling

```python
from imblearn.over_sampling import RandomOverSampler

# For use with numpy arrays, not generators
ros = RandomOverSampler(random_state=42)
X_resampled, y_resampled = ros.fit_resample(X_train, y_train)
```

## 📈 Expected Performance

**Baseline CNN**: 60-65% accuracy  
**Mini-XCEPTION**: 65-70% accuracy  
**State-of-the-art**: 70-75% accuracy

The dataset is challenging due to:
- Low resolution (48x48)
- Grayscale images
- Class imbalance
- Label noise

## 🎯 Tips for Better Results

1. **Data Augmentation**: Essential due to limited data
   - Rotation, shifting, flipping
   - But avoid extreme augmentations that change emotion

2. **Transfer Learning**: Use pre-trained models
   - VGG-Face
   - FaceNet
   - ArcFace

3. **Ensemble Methods**: Combine multiple models
   - DeepFace + Custom CNN
   - Voting or averaging predictions

4. **Preprocessing**:
   - Face alignment
   - Histogram equalization
   - Noise reduction

5. **Architecture**:
   - Mini-XCEPTION is proven effective
   - ResNet variants
   - EfficientNet

## 📚 References

- Original Paper: "Challenges in Representation Learning: A report on three machine learning contests" (ICML 2013)
- Kaggle Dataset: https://www.kaggle.com/datasets/msambare/fer2013
- Mini-XCEPTION: https://github.com/oarriaga/face_classification

## 🔗 Integration with Main Application

To use your trained model in the main application:

1. Train your model and save it as `.h5` or `.hdf5`
2. Place it in the project root directory
3. Update `src/config.py`:
   ```python
   MODEL_PATH = 'path/to/your/model.h5'
   ```
4. Ensure the model input shape matches (48x48 for FER2013)
5. Run the application

The analyzer will automatically load and use your custom model!

---

<p align="center">
  Happy Training! 🚀
</p>

<p align="center">
  Questions? Contact <a href="mailto:admin@shayantaherkhani.ir">admin@shayantaherkhani.ir</a>
</p>
