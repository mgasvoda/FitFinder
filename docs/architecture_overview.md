# Closet Assistant App - Core Architecture Overview

## Objective
A multimodal AI-powered assistant to help users (starting with a closet inventory use case) manage clothing items, generate outfit suggestions, and search for inspiration. Designed for web-first deployment with an Android mobile wrapper via Capacitor. Code is being developed with heavy AI assistance (e.g., Windsurfer or similar).

## Top-Level System Overview

**Frontend:**
- Web-based chat UI (Next.js)
- File/image upload support
- Displays generated outfit suggestions (image + text)
- Responsive layout for future mobile compatibility

**Backend:**
- FastAPI server to handle API routing
- LangGraph agent framework for managing AI reasoning
- Tools exposed to agent:
  - Image captioning
  - Vector search (outfit matching)
  - Web search (fashion inspiration)
  - Image/file storage management

**Database & Storage:**
- SQLite for structured metadata
- Chroma for vector similarity search (CLIP embeddings)
- Local filesystem storage for images

**AI Models:**
- **Image Captioning:** BLIP / OFA / OpenAI Vision API
- **Text Embeddings:** OpenAI Embeddings / CLIP / MiniCLIP
- **Search Reasoning and Text Generation:** GPT-4o or similar

**Mobile Deployment:**
- Capacitor to wrap the web app for Android deployment
- Access to mobile features (e.g., image picker) via Capacitor plugins

## Core Components

**Agent Architecture:**
- Inputs: Text, Image
- Actions:
  - Parse intent from user input
  - Choose tool(s) dynamically based on prompt
  - Call tool APIs (image captioning, vector search, web search)
  - Aggregate results
  - Generate chat response

**Primary Tools:**
- `ImageCaptionerTool(image) -> description`
- `OutfitSearchTool(query_text, optional_image) -> matching_items`
- `WebSearchTool(query_text) -> links/snippets`
- `ImageStorageTool(uploaded_image) -> storage_location + metadata`

**Example User Flows:**
- Upload clothing item → Generate description → Store in DB
- Ask "Show me outfits for a summer party" → Search DB for matches
- Upload selfie → Find matching outfits based on colors/styles

## API Endpoints

**1. POST `/api/upload`**
- Upload an image of a clothing item.
- Input: multipart/form-data (image file)
- Output: JSON `{ description: string, image_url: string, item_id: string }`

**2. POST `/api/chat`**
- Submit a multimodal prompt (text + optional image) to the assistant.
- Input: JSON `{ prompt: string, optional_image_url?: string }`
- Output: JSON `{ response_text: string, matching_outfits?: array }`

**3. GET `/api/items/{item_id}`**
- Fetch metadata and image for a specific clothing item.
- Input: URL param `item_id`
- Output: JSON `{ id: string, description: string, image_url: string, tags: array }`

## API Schemas

**ChatRequest**
```python
class ChatRequest(BaseModel):
    prompt: str
    optional_image_url: Optional[str] = None
```

**ChatResponse**
```python
class ChatResponse(BaseModel):
    response_text: str
    matching_outfits: Optional[List[Dict[str, Any]]] = None
```

**UploadResponse**
```python
class UploadResponse(BaseModel):
    description: str
    image_url: str
    item_id: str
```

**ItemResponse**
```python
class ItemResponse(BaseModel):
    id: str
    description: str
    image_url: str
    tags: List[str]
```

## Project Layout (Tentative)

```
/closet-assistant/
├── frontend/
│   ├── pages/
│   ├── components/
│   └── services/api.js
├── backend/
│   ├── main.py (FastAPI server)
│   ├── agent/
│   │   ├── agent_core.py
│   │   └── tools/
│   │       ├── image_captioner.py
│   │       ├── outfit_searcher.py
│   │       ├── web_searcher.py
│   │       └── image_storage.py
│   ├── db/
│   │   ├── models.py
│   │   └── vector_store.py
│   └── services/
│       ├── embedding_service.py
│       └── storage_service.py
├── mobile/
│   ├── capacitor.config.json
│   └── android/
└── README.md
```

## Priorities for AI-Assisted Code Generation
1. Create clear interfaces for each Tool.
2. Isolate model inference (e.g., captioning, embedding) behind service classes.
3. Provide simple, clean API endpoints for frontend communication.
4. Document API input/output formats clearly to assist future code generation.
5. Prefer modular, composable functions wherever possible.

## Stretch Features (Post-MVP)
- Outfit rating and feedback loops ("I liked this one!")
- More advanced outfit generation (mixing user's wardrobe with online ideas)
- User closet "calendar" (track outfits over time)
- Style profile personalization
- Push notifications via mobile

---

# Quick Callouts for Model Context Usage
- Prioritize modular service- and tool-oriented code generation.
- Maintain a clear separation between backend logic and frontend presentation.
- Assume future plugin extensions (especially around mobile features) and code defensively.
- Start web-first and assume eventual Capacitor Android deployment.
- Agent must handle multimodal input selection flexibly: text only, image only, or text+image prompts.
