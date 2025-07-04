from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import subprocess
import threading
from typing import Dict, Any
import asyncio
from contextlib import asynccontextmanager

from app.utils.logger import app_logger
from app.utils.exceptions import AILLMSafetyException
from app.models.model_manager import ModelManager
from app.services.detection_service import DetectionService
from app.services.chat_service import ChatService
from app.api.chat import chat_router
from app.api.detectors import detector_router  
from app.api.config import config_router

# Try to import NeMo Guardrails, fall back to simple implementation
try:
    from app.guardrails.guardrails_manager import GuardrailsManager
    NEMO_AVAILABLE = True
except ImportError:
    from app.guardrails.simple_guardrails import SimpleGuardrails as GuardrailsManager
    NEMO_AVAILABLE = False
    app_logger.warning("NeMo Guardrails not available, using simplified implementation")

# Global instances
model_manager: ModelManager = None
detection_service: DetectionService = None
chat_service: ChatService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_manager, detection_service, chat_service
    
    app_logger.info("Starting AI Safety System...")
    
    try:
        # Initialize model manager
        model_manager = ModelManager()
        await model_manager.initialize()
        
        # Initialize services
        detection_service = DetectionService(model_manager)
        chat_service = ChatService(model_manager, detection_service)
        await chat_service.initialize()
        
        # Store in app state
        app.state.model_manager = model_manager
        app.state.detection_service = detection_service
        app.state.chat_service = chat_service
        
        app_logger.info(f"AI Safety System initialized successfully (NeMo: {NEMO_AVAILABLE})")
        
    except Exception as e:
        app_logger.error(f"Failed to initialize AI Safety System: {e}")
        raise
    
    yield
    
    # Cleanup
    app_logger.info("Shutting down AI Safety System...")
    if model_manager:
        await model_manager.cleanup()

app = FastAPI(
    title="AI Safety System",
    description="Local AI Safety System with Multiple Detectors",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - simplified for Streamlit only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(AILLMSafetyException)
async def safety_exception_handler(request, exc: AILLMSafetyException):
    return JSONResponse(
        status_code=400,
        content={
            "error": "AI Safety Error",
            "message": exc.message,
            "error_code": exc.error_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    app_logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

# Include routers
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(detector_router, prefix="/api/detectors", tags=["detectors"])
app.include_router(config_router, prefix="/api/config", tags=["config"])

@app.get("/")
async def root():
    return {
        "message": "AI Safety System Backend", 
        "status": "running",
        "streamlit_interface": "http://localhost:8501",
        "nemo_guardrails": NEMO_AVAILABLE
    }

@app.get("/api")
async def api_root():
    return {
        "message": "AI Safety System API", 
        "status": "running",
        "nemo_guardrails": NEMO_AVAILABLE
    }

@app.get("/health")
async def health_check():
    try:
        status = {
            "status": "healthy",
            "models_loaded": bool(model_manager and model_manager.is_initialized),
            "detectors_available": [],
            "ollama_connected": False,
            "nemo_guardrails": NEMO_AVAILABLE
        }
        
        if model_manager:
            status["detectors_available"] = list(model_manager.get_available_detectors().keys())
            status["ollama_connected"] = await model_manager.ollama_client.health_check()
            
        return status
    except Exception as e:
        app_logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app_logger.info("WebSocket connection established")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "chat_message":
                message = data.get("message", "")
                detector_config = data.get("detector_config", {})
                
                try:
                    # Process message through safety pipeline
                    response = await chat_service.process_message(message, detector_config)
                    await websocket.send_json(response)
                    
                except Exception as e:
                    app_logger.error(f"Error processing chat message: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to process message",
                        "error": str(e)
                    })
            
    except WebSocketDisconnect:
        app_logger.info("WebSocket connection closed")
    except Exception as e:
        app_logger.error(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
