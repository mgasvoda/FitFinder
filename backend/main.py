from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.agent.agent_core import agent_router
from backend.db.models import Base, engine
import os

app = FastAPI(title="FitFinder Backend")

# CORS setup for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure image storage directory exists
os.makedirs("images", exist_ok=True)

# DB init
Base.metadata.create_all(bind=engine)

# Mount agent (API) router
app.include_router(agent_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "FitFinder backend running"}
