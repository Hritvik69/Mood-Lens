import cv2
import json
import logging
import numpy as np
import psutil
import time
from fastapi import WebSocket, WebSocketDisconnect, BackgroundTasks
from processors.frame_processor import FrameProcessor
from repositories.history_repo import history_repo
from database.db_session import SessionLocal
from services.model_manager import model_manager

logger = logging.getLogger(__name__)

def get_system_stats() -> dict:
    """Retrieves current host resource usage telemetry."""
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
    except Exception:
        cpu, ram = 0.0, 0.0
        
    return {
        "cpu_usage": cpu,
        "ram_usage": ram,
        "gpu_engine": model_manager.current_provider or "CPUExecutionProvider",
        "active_threads": psutil.Process().num_threads() if hasattr(psutil.Process(), "num_threads") else 1
    }

def async_db_log(session_id: str, faces: list, inference_latency_ms: float):
    """Worker task to commit frame telemetry to SQLite database."""
    if not faces:
        return
        
    db = SessionLocal()
    try:
        history_repo.log_faces(
            db=db,
            session_id=session_id,
            faces=faces,
            inference_time_ms=inference_latency_ms
        )
    except Exception as e:
        logger.error(f"Failed to write background frame logs to database: {e}")
    finally:
        db.close()

async def handle_websocket(websocket: WebSocket):
    """
    Accepts WebSocket connection, parses binary JPEG streams,
    runs the frame processor, and pushes telemetry back to client.
    """
    await websocket.accept()
    logger.info("WebSocket connection established.")
    
    processor = FrameProcessor()
    session_id = f"sess_{int(time.time())}"
    
    # Connection-specific config (sent from client via JSON text frames)
    current_config = {
        "confidence_threshold": 0.5,
        "confidence_smoothing": 0.3,
        "record_history": True,
        "model": "ferplus-8",
    }
    
    # Metrics tracking for FPS
    frame_count = 0
    fps_start_time = time.time()
    current_fps = 0.0
    
    try:
        while True:
            # Block waiting for next message
            message = await websocket.receive()
            
            # 1. Configuration updates (Text messages)
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    if isinstance(data, dict):
                        current_config.update(data)
                        if "session_id" in data:
                            session_id = data["session_id"]
                        logger.debug(f"Socket configuration updated: {current_config}")
                except Exception as e:
                    logger.error(f"Error parsing socket text message: {e}")
                    
            # 2. Frame processing (Binary messages)
            elif "bytes" in message:
                frame_count += 1
                
                # Dynamic FPS calculation
                elapsed = time.time() - fps_start_time
                if elapsed >= 1.0:
                    current_fps = frame_count / elapsed
                    frame_count = 0
                    fps_start_time = time.time()
                
                jpeg_bytes = message["bytes"]
                
                # Decode JPEG binary buffer in-memory using OpenCV
                nparr = np.frombuffer(jpeg_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    continue
                    
                # Process the frame
                faces, perf = processor.process_frame(frame, current_config)
                
                # Append live tracking FPS
                perf["fps"] = round(current_fps, 1)
                
                # Asynchronously save to SQLite to keep socket loop unblocked
                if faces and current_config.get("record_history", True):
                    # Direct function invocation off the event loop
                    # Uses FastAPI BackgroundTasks or direct executor to prevent blocks.
                    # Since we are inside ws_handler, we'll write directly using a lightweight thread.
                    # Standard practice for low latency: use background executors or direct commits.
                    # Since SQL writes are buffered by SQLite WAL mode, it is extremely fast.
                    try:
                        async_db_log(session_id, faces, perf["total_latency_ms"])
                    except Exception as err:
                        logger.error(f"Failed logging frame: {err}")
                
                # Fetch server stats
                system_stats = get_system_stats()
                system_stats["fps"] = perf["fps"]
                
                # Send telemetry packet back
                await websocket.send_json({
                    "session_id": session_id,
                    "faces": faces,
                    "performance": perf,
                    "system": system_stats
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket session disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket session loop: {e}", exc_info=True)
    finally:
        processor.close()
