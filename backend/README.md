# FitFinder Backend Skeleton

# Directory Structure
# backend/
#   main.py
#   agent/
#     agent_core.py
#     tools/
#       image_captioner.py
#       outfit_searcher.py
#       web_searcher.py
#       image_storage.py
#   db/
#     models.py
#     vector_store.py
#   services/
#     embedding_service.py
#     storage_service.py
#   tests/
#     test_main.py
# requirements.txt

# This README describes the backend skeleton and development workflow.

## Overview
This backend is a modular FastAPI application, following the architecture in `docs/architecture_overview.md`. It supports multimodal chat, image upload, and outfit search, and is ready for AI agent orchestration and future extensibility.

## Key Technologies
- FastAPI (API server)
- Pydantic (API schemas)
- SQLite (structured storage)
- Chroma (vector similarity search)
- LangGraph (agent orchestration)
- Local filesystem for images

## Directory Layout
- `main.py`: FastAPI entrypoint and API routes
- `agent/`: Agent orchestration and tool APIs
- `db/`: Database models and vector store logic
- `services/`: Modular services for embedding, storage, etc.
- `tests/`: Unit/integration test skeletons

## Quickstart
1. Install requirements: `pip install -r requirements.txt`
2. Run the server: `uvicorn backend.main:app --reload`
3. Run tests: `pytest backend/tests/`

## API Endpoints
- `POST /api/upload`: Upload clothing item image
- `POST /api/chat`: Multimodal prompt to AI assistant
- `GET /api/items/{item_id}`: Fetch clothing item metadata/image

## Contribution
- Follow modular, composable, and testable code practices.
- Use Pydantic for all API schemas.
- Add/modify tools/services in their respective directories.
- Write or update tests for all new features.

---
See `docs/architecture_overview.md` for detailed architecture and priorities.
