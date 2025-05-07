# LangGraph Agent Graph Structure

A structured overview of tools and function nodes, and how they connect in the FitFinder LangGraph agent.

---

## Tools

- **caption_image**:  Generate a caption from an image using the external vision model.
- **search_items**:  Perform vector similarity search in the "clothing_items" collection to find item IDs.
- **search_outfits**:  Perform vector similarity search in the "outfits" collection to find outfit IDs.
- **create_outfit**:  Business logic to assemble and persist a new outfit via CRUD.
- **embed_text**:  Generate text embeddings for arbitrary text input (used by search tools).
- **embed_image**:  Generate image embeddings for arbitrary image input (used by search tools).

## Function Nodes

- `store_image(state)` &rarr; writes image file to disk, returns `image_url`.
- `get_text_embedding(text)` &rarr; calls `embedding_service` to get vector.
- `get_image_embedding(image_url)` &rarr; calls `embedding_service` for image.
- `crud.create_clothing_item(params)` &rarr; persists metadata to SQLite.
- `crud.get_clothing_items_by_ids(item_ids)` &rarr; loads item metadata.
- `crud.create_outfit(params)` &rarr; persists outfit composition.
- `crud.get_outfits_by_ids(outfit_ids)` &rarr; loads outfit metadata.
- `format_item_search_response(items)` &rarr; shapes search results for the agent reply.
- `format_outfit_response(outfits)` &rarr; shapes outfit results for the agent reply.

## Dispatcher / Choice Node

A `ChoiceNode` inspects the last tool call name and routes to the correct tool node.

```python
# pseudo-code
last_tool = inputs['messages'][-1].tool_calls[-1]['name']
return last_tool
```

## Graph Sketch

```text
[User Input]
     ↓
[Dispatcher]
    ├─ "caption_image" ──▶ [CaptionToolNode]
    │                         ↓
    │                   [EmbedImageNode]
    │                         ↓
    │                   [PersistClothingItemNode]
    │                         ↓
    │                   [FormatResponseNode]
    │
    ├─ "search_items" ───▶ [SearchItemsToolNode]
    │                         ↓
    │                   [GetItemsNode]
    │                         ↓
    │                   [FormatItemSearchResponse]
    │
    ├─ "create_outfit" ──▶ [CreateOutfitToolNode]
    │                         ↓
    │                   [PersistOutfitNode]
    │                         ↓
    │                   [FormatOutfitCreationResponse]
    │
    └─ "search_outfits" ─▶ [SearchOutfitsToolNode]
                              ↓
                         [GetOutfitsNode]
                              ↓
                         [FormatOutfitResponse]
```

---

*This sketch preserves your existing caption → embed → persist flow and extends to search, outfit creation, and outfit search. Each tool is a standalone node, with shared function nodes for common logic.*
