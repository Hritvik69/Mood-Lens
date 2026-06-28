import logging
import uvicorn
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import setup_logging
from database.db_session import init_db
from services.model_manager import model_manager
from api.ws_handler import handle_websocket
from api.routers import history, analytics

# Setup logging configuration
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time AI Facial Expression & Feature Analytics Server",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST endpoints routers
app.include_router(history.router)
app.include_router(analytics.router)

@app.on_event("startup")
def on_startup():
    logger.info("Starting up server...")
    
    # 1. Initialize SQLite Database Tables
    logger.info("Initializing SQLite database tables...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Critical: Database initialization failed: {e}")
        
    # 2. Preload & Warmup ONNX Model
    logger.info("Preloading AI models...")
    try:
        model_manager.load_model()
        logger.info("AI models preloaded and warmed up successfully.")
    except Exception as e:
        logger.critical(
            f"Failed to preload AI models: {e}. "
            f"The server is running, but real-time classification will fail until corrected."
        )

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Server shutting down. Releasing resources...")

@app.get("/api/health")
def get_health():
    """Simple service health check endpoint."""
    model_loaded = model_manager.session is not None
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "model_loaded": model_loaded,
        "execution_provider": model_manager.current_provider if model_loaded else None
    }

# Register WebSocket Endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await handle_websocket(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False  # Disabled in production for performance
    )
