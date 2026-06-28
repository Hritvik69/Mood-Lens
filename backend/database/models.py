from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FrameLog(Base):
    __tablename__ = "frame_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Face details
    face_id = Column(Integer, nullable=False, index=True)
    expression = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Eye contact & Blinks
    eye_contact = Column(Boolean, default=False)
    smile_intensity = Column(Float, default=0.0)
    mouth_openness = Column(Float, default=0.0)
    blink_rate = Column(Float, default=0.0)
    drowsiness_detected = Column(Boolean, default=False)
    
    # Pose & Spatial
    head_pose_pitch = Column(Float, default=0.0)
    head_pose_yaw = Column(Float, default=0.0)
    head_pose_roll = Column(Float, default=0.0)
    face_distance = Column(Float, default=0.0)
    
    # Quality metrics
    lighting_score = Column(Float, default=0.0)
    blur_score = Column(Float, default=0.0)
    centering_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    
    # Performance
    inference_time_ms = Column(Float, default=0.0)
