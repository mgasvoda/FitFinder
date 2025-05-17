# FitFinder

A smart outfit recommendation system that helps you find the perfect outfit from your wardrobe using AI.

## Project Structure

- `backend/` - FastAPI backend with AI agent orchestration
- `frontend/` - Next.js frontend application
- `docs/` - Project documentation and architecture

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend development)
- Poetry (for Python dependency management)

## Backend Setup

1. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the development server:
   ```bash
   poetry run uvicorn backend.main:app --reload
   ```

## Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

## Development

- Run tests:
  ```bash
  poetry run pytest
  ```

- Format code:
  ```bash
  poetry run black .
  poetry run isort .
  ```

- Type checking:
  ```bash
  poetry run mypy .
  ```

## Deployment

This project is configured for deployment on Render. The `render.yaml` file contains the deployment configuration.

## License

MIT
