# Outfit Generation Agent Design (LangGraph)

This document defines the design for a LangGraph-based outfit generation agent. It supports both initial outfit creation and iterative user-driven refinement. It is intended for use in Windsurf as architectural context when building prompts or logic extensions.

## Overview

The agent generates seasonal fashion outfits from a clothing item metadata database (SQLite) and a corresponding ChromaDB collection of item embeddings. Users can prompt the system with natural language queries like:

> "Create a spring outfit using white pants"

The system will assemble a complete outfit using metadata filters and embedding-based similarity, then support iterative user feedback such as:

> "Swap the shoes for something more formal"

## Goals

* Assemble complete, seasonally appropriate outfits
* Support iterative refinement through user feedback
* Ensure outputs always meet minimum outfit requirements (top, bottom, shoes)
* Reuse existing tool implementations for data access and item embedding

## Components

### Tools (Reused)

The graph assumes these tools exist and will re-use their implementations:

* `query_sqlite_by_tags(tags: dict) -> list[item_id]`
* `query_chroma_by_ids_and_embedding(ids: list, embedding: list, top_k: int) -> list[item]`
* `get_item_embedding(text: str) -> list[float]`
* `check_outfit_completeness(items: list[item]) -> bool`

### Graph State

The graph operates over a mutable `outfit_state` object, which contains:

```python
outfit_state = {
  "selected_items": list[item],         # Items currently in the outfit
  "missing_categories": list[str],      # e.g., ["top", "shoes"]
  "feedback_log": list[str],           # User refinement requests
  "season": str,                        # Extracted from prompt
  "anchor_item_description": str        # Initial user-provided item (e.g. "white pants")
}
```

## Graph Flow

```plaintext
[Start: User Prompt]
      ↓
[Parse Tags + Get Embedding for Anchor Item]
      ↓
[Query SQLite for Anchor Item Candidates]
      ↓
[Query Chroma for Best Match to Anchor Item]
      ↓
[Update Outfit State → Add Anchor Item]
      ↓
[Loop: Add Missing Categories]
      ↓
[Check Outfit Completeness]
      ↓
[Prompt for Feedback or Return Final Result]
      ↓
[If Feedback → Handle Feedback → Replace Items → Loop Back]
```

## Key Logic Nodes

### `build_outfit_from_anchor`

Builds the outfit by iteratively identifying missing categories and selecting suitable items using metadata filters and embedding proximity.

### `handle_user_feedback`

Parses user feedback (e.g. "replace the shoes") and updates `outfit_state` to:

* Remove specified item category
* Add any new style constraints
* Re-enter the outfit assembly loop from that point

### `finalize_or_refine`

Checks whether user feedback was received. If so, re-enters refinement; otherwise returns the current outfit.

## Termination Conditions

* The graph **must always pass through** `check_outfit_completeness` before returning.
* The user may issue feedback multiple times; the loop continues until no further refinement is requested.

## Notes

* Output should be formatted as a structured object or JSON, not freeform prose.
* The agent should never return an outfit missing required categories.
* Any replacement must maintain metadata compatibility (e.g., season match).

## Future Extensions

* Support style modifiers (e.g., "make it casual", "business-ready")
* Incorporate user-specific preferences or wardrobe constraints
* Suggest accessories or complementary colors using secondary filters

