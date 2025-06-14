from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from backend.agent.agent_core import agent_router, stream_graph_updates
from backend.core import core_router
from backend.db.models import Base, engine
from backend.db import vector_store
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv("API_KEY", "default-super-secret-key")  # Change this in production
API_KEY_NAME = "X-API-Key"

app = FastAPI(title="FitFinder Backend", docs_url="/api/docs", redoc_url="/api/redoc")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-api-key", "X-API-Key"],  # Explicitly expose the API key header
)

# API Key validation
async def verify_api_key(request: Request):
    logger.info(f"Headers: {request.headers}")
    # Try to get API key from headers (case-insensitive)
    api_key = request.headers.get('X-API-Key') or request.headers.get('x-api-key')
    
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return api_key

# Ensure image storage directory exists
os.makedirs("images", exist_ok=True)

# DB init
Base.metadata.create_all(bind=engine)
# ChromaDB embedding collections init
vector_store.init_chroma_collections()

# Mount routers with API key protection
app.include_router(agent_router, prefix="/api", dependencies=[Depends(verify_api_key)])
# app.include_router(core_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "FitFinder backend running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import socket
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Get local IP address for better logging
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        logger.info(f"Local IP address: {local_ip}")
        logger.info(f"Network IP address: 192.168.1.171")
    except Exception as e:
        logger.warning(f"Could not determine local IP: {e}")
    
    logger.info(f"Starting server on http://{host}:{port}")
    logger.info(f"API Documentation available at http://{host}:{port}/api/docs")
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
    