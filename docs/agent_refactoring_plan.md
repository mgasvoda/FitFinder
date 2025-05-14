# Agent Refactoring Plan: Improving Maintainability and Separation of Concerns

## Background

As the agent functionality has grown, `agent_core.py` and `langgraph_agent.py` have become complex and tightly coupled. This plan outlines a restructuring approach to improve maintainability, testability, and alignment with the project's architectural principles (see `architecture_overview.md`).

---

## 1. Architectural Principles
- **Separation of Concerns**: Distinct boundaries between API, agent orchestration, tools, and model inference.
- **Modularity**: Prefer small, composable functions and clear interfaces.
- **Service Layer**: Model inference (captioning, embedding, etc.) should be behind service classes.
- **API Layer**: FastAPI endpoints should focus on request/response handling only.
- **Tool Layer**: Each tool (captioning, search, storage, etc.) in its own module.
- **Agent Layer**: Orchestration logic (LangGraph) should be isolated from API and tools.

---

## 2. Current Issues
- Endpoint functions in `agent_core.py` contain agent orchestration and business logic.
- Pydantic schemas are mixed with endpoint and orchestration code.
- Step functions and tool orchestration are tightly coupled in `langgraph_agent.py`.
- Tool definitions, graph logic, and step logic are not clearly separated.

---

## 3. Target Structure

```
backend/
  agent/
    __init__.py
    agent_core.py        # FastAPI endpoints only
    schemas.py           # Pydantic models
    orchestrator.py      # Agent orchestration (LangGraph, etc.)
    steps.py             # All agent step functions (embed_step, persist_db_step, etc.)
    tools/
      caption_image.py
      image_storage.py
      outfit_searcher.py
      ...
  services/
    embedding_service.py
    storage_service.py
  db/
    models.py
    crud.py
```

---

## 4. Refactoring Steps

1. **Extract Pydantic Schemas**
   - Move all Pydantic models (e.g., `ChatRequest`, `ChatResponse`, etc.) from `agent_core.py` to `schemas.py`.

2. **Consolidate Step Functions**
   - Move all agent step functions (e.g., `embed_step`, `persist_db_step`, `get_items_step`) from `langgraph_agent.py` to a new `steps.py` file.
   - Each step should be a pure function or class, easily testable and reusable.

3. **Modularize Tools**
   - Ensure each tool (captioning, search, storage, etc.) is a class/function in its own file under `tools/`.
   - Tool interfaces should be consistent and documented.

4. **Refactor Agent Orchestration**
   - Move LangGraph graph construction and execution into `orchestrator.py`.
   - Orchestrator should expose a clean interface (e.g., `run_agent(state: dict) -> dict`).

5. **Refactor API Endpoints**
   - Endpoints in `agent_core.py` should only handle HTTP request/response, validation, and error handling.
   - Delegate all business logic to the orchestrator/service layer.

6. **Improve Logging and Error Handling**
   - Centralize logging configuration.
   - Use structured logging for agent steps and tool invocations.
   - Standardize error handling and propagate meaningful errors to the API layer.

7. **Documentation and Typing**
   - Document interfaces for each step, tool, and orchestrator.
   - Use type annotations everywhere for clarity and maintainability.

---

## 5. Benefits
- **Maintainability**: Each concern is isolated and easier to update/test.
- **Readability**: Clearer code boundaries, less cognitive load.
- **Extensibility**: New tools/steps can be added with minimal changes elsewhere.
- **Testability**: Each step/tool can be tested in isolation.

---

## 6. Notes
- For now, all agent step functions will be consolidated in a single `steps.py` file for simplicity, as the number of steps is expected to remain manageable.
- This plan is intended as context for future refactoring and should be referenced when making structural changes to the agent codebase.

---

_Last updated: 2025-05-12_
