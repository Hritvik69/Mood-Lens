from fastapi import APIRouter, HTTPException, Query
from repositories.analytics_repo import analytics_repo

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary")
def get_analytics_summary():
    """Fetches high-level metrics across all historical logs."""
    try:
        metrics = analytics_repo.get_summary_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load summary analytics: {e}")

@router.get("/distribution")
def get_expression_distribution():
    """Fetches facial expression occurrences and average confidence values."""
    try:
        dist = analytics_repo.get_expression_distribution()
        return dist
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load expression distribution: {e}")

@router.get("/timeline")
def get_analytics_timeline(
    interval: int = Query(5, ge=1, le=60, description="Grouping interval in minutes")
):
    """Fetches facial expression occurrences mapped onto a time series."""
    try:
        timeline = analytics_repo.get_timeline_metrics(interval_minutes=interval)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load timeline analytics: {e}")

@router.get("/quality")
def get_quality_analytics():
    """Fetches aggregate details on lighting, blur, centering, and distance scores."""
    try:
        quality = analytics_repo.get_quality_over_time()
        return quality
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load quality analytics: {e}")
