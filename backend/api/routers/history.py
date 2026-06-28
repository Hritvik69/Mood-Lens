from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from database.db_session import get_db
from repositories.history_repo import history_repo

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("")
def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    session_id: str = Query(None),
    expression: str = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieves a paginated list of face detection logs."""
    try:
        logs, total = history_repo.get_logs(
            db=db, page=page, limit=limit, session_id=session_id, expression=expression
        )
        
        # Serialize logs to simple dictionary list
        serialized_logs = []
        for log in logs:
            serialized_logs.append({
                "id": log.id,
                "session_id": log.session_id,
                "timestamp": log.timestamp.isoformat(),
                "face_id": log.face_id,
                "expression": log.expression,
                "confidence": round(log.confidence, 4),
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
            
        return {
            "page": page,
            "limit": limit,
            "total": total,
            "results": serialized_logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failure: {e}")

@router.delete("")
def clear_history(db: Session = Depends(get_db)):
    """Deletes all logged history records from the database."""
    try:
        history_repo.clear_history(db)
        return {"status": "success", "message": "History cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear history: {e}")

@router.get("/export/csv")
def export_history_csv(db: Session = Depends(get_db)):
    """Exports all logs as a downloadable CSV file."""
    try:
        csv_data = history_repo.export_csv(db)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=emotionvision_history.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {e}")

@router.get("/export/json")
def export_history_json(db: Session = Depends(get_db)):
    """Exports all logs as a downloadable JSON file."""
    try:
        json_data = history_repo.export_json(db)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=emotionvision_history.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export JSON: {e}")
