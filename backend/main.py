from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from backend.agent.agent_core import agent_router
from backend.core import core_router
from backend.db.models import Base, engine
from backend.db import vector_store
import os

# Configuration
API_KEY = os.getenv("API_KEY", "default-super-secret-key")  # Change this in production
API_KEY_NAME = "X-API-Key"

app = FastAPI(title="FitFinder Backend", docs_url="/api/docs", redoc_url="/api/redoc")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key validation
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
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
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
    