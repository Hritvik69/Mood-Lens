import cv2
import numpy as np
import math
from typing import List, Dict, Any, Tuple

class HeadPoseEstimator:
    """
    Computes Pitch, Yaw, and Roll Euler angles from 2D facial landmarks 
    using Perspective-n-Point (solvePnP) with a standard 3D face model.
    """
    
    def __init__(self):
        # 3D model points of standard human face in arbitrary space
        # Nose tip, Chin, Left Eye Corner, Right Eye Corner, Left Mouth Corner, Right Mouth Corner
        self.model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip (landmark 1)
            (0.0, -330.0, -65.0),        # Chin (landmark 152)
            (-225.0, 170.0, -135.0),     # Left Eye corner (landmark 33)
            (225.0, 170.0, -135.0),      # Right Eye corner (landmark 263)
            (-150.0, -150.0, -125.0),    # Left Mouth corner (landmark 61)
            (150.0, -150.0, -125.0)      # Right Mouth corner (landmark 291)
        ], dtype=np.float32)

    def estimate_pose(
        self, 
        landmarks: List[List[float]], 
        width: int, 
        height: int
    ) -> Tuple[float, float, float, float]:
        """
        Estimates the head pose.
        
        Returns:
            pitch: Rotation around the X-axis (nodding up/down)
            yaw: Rotation around the Y-axis (turning left/right)
            roll: Rotation around the Z-axis (tilting left/right)
            distance: Estimate of face distance from camera in meters
        """
        # Map indices to pixels
        image_points = np.array([
            (landmarks[1][0] * width, landmarks[1][1] * height),       # Nose tip
            (landmarks[152][0] * width, landmarks[152][1] * height),   # Chin
            (landmarks[33][0] * width, landmarks[33][1] * height),     # Left Eye
            (landmarks[263][0] * width, landmarks[263][1] * height),   # Right Eye
            (landmarks[61][0] * width, landmarks[61][1] * height),     # Left Mouth corner
            (landmarks[291][0] * width, landmarks[291][1] * height)    # Right Mouth corner
        ], dtype=np.float32)

        # Camera internals approximation
        focal_length = width
        center = (width / 2, height / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float32)

        # Assuming no lens distortion
        dist_coeffs = np.zeros((4, 1))

        # Solve Perspective-n-Point (PnP)
        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.model_points, 
            image_points, 
            camera_matrix, 
            dist_coeffs, 
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return 0.0, 0.0, 0.0, 1.0

        # Calculate translation distance (Z axis is depth)
        # Convert model coordinates ratio to approximate real-world meters
        # Model eyes width is 450 units. Real eyes width is ~0.065 meters (6.5cm).
        # Scale = 0.065 / 450.0
        tz = translation_vector[2][0]
        distance_meters = float(tz * (0.065 / 450.0))
        # Ensure minimum distance
        distance_meters = max(0.2, distance_meters)

        # Convert rotation vector to rotation matrix
        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

        # Extract Euler angles from rotation matrix
        sy = math.sqrt(rotation_matrix[0,0] * rotation_matrix[0,0] + rotation_matrix[1,0] * rotation_matrix[1,0])
        singular = sy < 1e-6

        if not singular:
            x = math.atan2(rotation_matrix[2,1], rotation_matrix[2,2])
            y = math.atan2(-rotation_matrix[2,0], sy)
            z = math.atan2(rotation_matrix[1,0], rotation_matrix[0,0])
        else:
            x = math.atan2(-rotation_matrix[1,2], rotation_matrix[1,1])
            y = math.atan2(-rotation_matrix[2,0], sy)
            z = 0

        # Convert to degrees
        pitch = x * 180.0 / math.pi
        yaw = y * 180.0 / math.pi
        roll = z * 180.0 / math.pi

        return round(pitch, 1), round(yaw, 1), round(roll, 1), round(distance_meters, 2)
