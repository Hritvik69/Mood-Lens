import duckdb
import logging
from typing import Dict, Any, List
from database.db_session import get_duckdb_conn

logger = logging.getLogger(__name__)

class AnalyticsRepository:
    """
    Leverages DuckDB to run aggregate analytical queries directly over SQLite database tables.
    """
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Returns high-level summary telemetry."""
        conn = get_duckdb_conn()
        try:
            # Query general averages
            res = conn.execute("""
                SELECT 
                    COUNT(*) as total_logs,
                    COUNT(DISTINCT session_id) as total_sessions,
                    AVG(confidence) * 100 as avg_confidence,
                    AVG(inference_time_ms) as avg_inference_time,
                    AVG(quality_score) as avg_quality,
                    SUM(CASE WHEN drowsiness_detected = 1 THEN 1 ELSE 0 END) as drowsiness_events
                FROM sqlite_db.frame_logs
            """).fetchone()
            
            if not res or res[0] == 0:
                return {
                    "total_detections": 0,
                    "total_sessions": 0,
                    "average_confidence": 0.0,
                    "average_inference_ms": 0.0,
                    "average_quality": 0.0,
                    "drowsiness_alerts": 0
                }
                
            return {
                "total_detections": int(res[0]),
                "total_sessions": int(res[1]),
                "average_confidence": round(float(res[2]), 2),
                "average_inference_ms": round(float(res[3]), 2),
                "average_quality": round(float(res[4]), 2),
                "drowsiness_alerts": int(res[5])
            }
        except Exception as e:
            logger.error(f"Failed to fetch summary metrics: {e}")
            return {}
        finally:
            conn.close()

    def get_expression_distribution(self) -> List[Dict[str, Any]]:
        """Returns frequency and average confidence for each facial expression."""
        conn = get_duckdb_conn()
        try:
            res = conn.execute("""
                SELECT 
                    expression, 
                    COUNT(*) as count,
                    AVG(confidence) * 100 as avg_conf
                FROM sqlite_db.frame_logs
                GROUP BY expression
                ORDER BY count DESC
            """).fetchall()
            
            total = sum(row[1] for row in res) if res else 0
            if total == 0:
                return []
                
            return [
                {
                    "expression": row[0],
                    "count": int(row[1]),
                    "percentage": round((row[1] / total) * 100, 2),
                    "average_confidence": round(float(row[2]), 2)
                } for row in res
            ]
        except Exception as e:
            logger.error(f"Failed to fetch expression distribution: {e}")
            return []
        finally:
            conn.close()

    def get_timeline_metrics(self, interval_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Groups detections in time buckets to build a live timeline.
        Uses SQLite datetime functions supported by DuckDB.
        """
        conn = get_duckdb_conn()
        try:
            # DuckDB allows using standard SQL grouping over time buckets
            # SQLite format: 2026-06-27T16:02:00
            query = f"""
                SELECT 
                    strftime('%Y-%m-%dT%H:%M:00', timestamp) as time_bucket,
                    COUNT(*) as detections_count,
                    AVG(confidence) * 100 as avg_confidence,
                    AVG(quality_score) as avg_quality,
                    AVG(smile_intensity) as avg_smile
                FROM sqlite_db.frame_logs
                GROUP BY time_bucket
                ORDER BY time_bucket ASC
                LIMIT 50
            """
            res = conn.execute(query).fetchall()
            return [
                {
                    "timestamp": row[0],
                    "count": int(row[1]),
                    "confidence": round(float(row[2]), 2),
                    "quality": round(float(row[3]), 2),
                    "smile_intensity": round(float(row[4]), 2)
                } for row in res
            ]
        except Exception as e:
            logger.error(f"Failed to fetch timeline metrics: {e}")
            return []
        finally:
            conn.close()

    def get_quality_over_time(self) -> Dict[str, List[float]]:
        """Fetches trend data for lighting, blur, and centering scores."""
        conn = get_duckdb_conn()
        try:
            res = conn.execute("""
                SELECT 
                    AVG(lighting_score), 
                    AVG(blur_score), 
                    AVG(centering_score),
                    AVG(face_distance)
                FROM sqlite_db.frame_logs
            """).fetchone()
            
            if not res or res[0] is None:
                return {"lighting": 0, "blur": 0, "centering": 0, "distance": 0}
                
            return {
                "lighting": round(float(res[0]), 2),
                "blur": round(float(res[1]), 2),
                "centering": round(float(res[2]), 2),
                "distance": round(float(res[3]), 2)
            }
        except Exception as e:
            logger.error(f"Failed to fetch quality distributions: {e}")
            return {}
        finally:
            conn.close()

analytics_repo = AnalyticsRepository()
