import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from database.models import FrameLog

class HistoryRepository:
    """
    Handles read/write transactions to the SQLite database for FrameLog records.
    """
    
    def log_faces(
        self, 
        db: Session, 
        session_id: str, 
        faces: List[Dict[str, Any]], 
        inference_time_ms: float
    ):
        """Saves logs for each detected face in the frame."""
        logs = []
        for face in faces:
            pose = face.get("pose", {})
            quality = face.get("quality", {})
            blink = face.get("blink_metrics", {})
            
            log = FrameLog(
                session_id=session_id,
                timestamp=datetime.utcnow(),
                face_id=face.get("face_id", 0),
                expression=face.get("expression", "Neutral"),
                confidence=face.get("expression_confidence", 1.0),
                eye_contact=blink.get("eye_contact", False),
                smile_intensity=blink.get("smile_intensity", 0.0),
                mouth_openness=blink.get("mouth_openness", 0.0),
                blink_rate=blink.get("blink_rate", 0.0),
                drowsiness_detected=blink.get("drowsiness_detected", False),
                head_pose_pitch=pose.get("pitch", 0.0),
                head_pose_yaw=pose.get("yaw", 0.0),
                head_pose_roll=pose.get("roll", 0.0),
                face_distance=face.get("distance", 0.0),
                lighting_score=quality.get("lighting", 0.0),
                blur_score=quality.get("blur", 0.0),
                centering_score=quality.get("centering", 0.0),
                quality_score=quality.get("score", 0.0),
                inference_time_ms=inference_time_ms
            )
            logs.append(log)
            
        try:
            db.bulk_save_objects(logs)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    def get_logs(
        self, 
        db: Session, 
        page: int = 1, 
        limit: int = 100, 
        session_id: str = None, 
        expression: str = None
    ) -> Tuple[List[FrameLog], int]:
        """Returns a paginated list of frame logs and the total count."""
        query = db.query(FrameLog)
        
        if session_id:
            query = query.filter(FrameLog.session_id == session_id)
        if expression:
            query = query.filter(FrameLog.expression == expression)
            
        total_count = query.count()
        
        offset = (page - 1) * limit
        results = query.order_by(FrameLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        return results, total_count

    def clear_history(self, db: Session):
        """Clears all history logs."""
        try:
            db.query(FrameLog).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    def export_csv(self, db: Session) -> str:
        """Exports all database logs as a CSV formatted string."""
        logs = db.query(FrameLog).order_by(FrameLog.timestamp.asc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            "ID", "SessionID", "Timestamp", "FaceID", "Expression", "Confidence",
            "EyeContact", "SmileIntensity", "MouthOpenness", "BlinkRate", "Drowsiness",
            "Pitch", "Yaw", "Roll", "DistanceMeters", "LightingScore", "BlurScore",
            "CenteringScore", "QualityScore", "InferenceTimeMs"
        ])
        
        for log in logs:
            writer.writerow([
                log.id, log.session_id, log.timestamp.isoformat(), log.face_id, log.expression, log.confidence,
                log.eye_contact, log.smile_intensity, log.mouth_openness, log.blink_rate, log.drowsiness_detected,
                log.head_pose_pitch, log.head_pose_yaw, log.head_pose_roll, log.face_distance, log.lighting_score,
                log.blur_score, log.centering_score, log.quality_score, log.inference_time_ms
            ])
            
        return output.getvalue()

    def export_json(self, db: Session) -> str:
        """Exports all database logs as a JSON formatted string."""
        logs = db.query(FrameLog).order_by(FrameLog.timestamp.asc()).all()
        
        serialized_logs = []
        for log in logs:
            serialized_logs.append({
                "id": log.id,
                "session_id": log.session_id,
                "timestamp": log.timestamp.isoformat(),
                "face_id": log.face_id,
                "expression": log.expression,
                "confidence": log.confidence,
                "eye_contact": log.eye_contact,
                "smile_intensity": log.smile_intensity,
                "mouth_openness": log.mouth_openness,
                "blink_rate": log.blink_rate,
                "drowsiness_detected": log.drowsiness_detected,
                "head_pose": {
                    "pitch": log.head_pose_pitch,
                    "yaw": log.head_pose_yaw,
                    "roll": log.head_pose_roll
                },
                "face_distance": log.face_distance,
                "quality": {
                    "lighting": log.lighting_score,
                    "blur": log.blur_score,
                    "centering": log.centering_score,
                    "score": log.quality_score
                },
                "inference_time_ms": log.inference_time_ms
            })
            
        return json.dumps(serialized_logs, indent=2)

history_repo = HistoryRepository()
