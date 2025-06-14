# FitFinder

A smart AI fashion assistant that helps you manage your wardrobe and create outfits using a conversational chat interface.

## 🌟 Features

- **Smart Wardrobe Management**: Add and organize clothing items with AI-powered descriptions
- **Outfit Creation**: Generate complete outfits based on your preferences and items
- **Natural Language Interface**: Chat with your AI fashion assistant using natural language
- **Secure Authentication**: User login system with role-based access
- **Vector Search**: Find similar items using advanced embedding-based search

## 🏗️ Project Structure

- `backend/` - Core application with AI agent and database
- `backend/auth/` - User authentication system
- `backend/agent/` - AI fashion assistant (LangGraph + Anthropic Claude)
- `backend/db/` - Database models and vector storage
- `docs/` - Project documentation

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Poetry (for dependency management)
- Anthropic API key

### 1. Install Dependencies

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your settings
# Required: Add your ANTHROPIC_API_KEY
```

### 3. Run FitFinder

**Option A: Simple startup script**
```bash
python start_fitfinder_chainlit.py
```

**Option B: Direct chainlit command**
```bash
chainlit run backend/chainlit_app.py --port 8001
```

### 4. Access the Interface

- Open your browser to `http://localhost:8001`
- Login with default credentials: `admin` / `fitfinder2024!`
- Start chatting with your AI fashion assistant!

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with these variables:

```bash
# Required: AI service API key
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Optional: Custom admin credentials
CHAINLIT_ADMIN_USERNAME=admin
CHAINLIT_ADMIN_PASSWORD=your-secure-password

# Optional: Database location
DATABASE_URL=sqlite:///./fitfinder.db
```

### User Management

Manage users with the built-in utility:

```bash
# Interactive user management
python -m backend.auth.user_manager

# Add a user via command line
python -m backend.auth.user_manager --add
```

## 🛠️ Development

### Testing the Agent

Test the AI agent directly in CLI mode:

```bash
python -m backend.agent.agent_core
```

### Code Quality

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy .
```

### Architecture

- **LangGraph Agent**: Orchestrates AI tools and conversation flow
- **Anthropic Claude**: Powers the conversational AI
- **SQLite**: Stores clothing items and outfit data
- **ChromaDB**: Vector database for similarity search
- **Chainlit**: Provides the chat interface and authentication

## 📚 Documentation

- [`AUTH_SETUP.md`](AUTH_SETUP.md) - Authentication setup and user management
- [`docs/`](docs/) - Architecture and development guides

## 🚀 Deployment

The application is configured for deployment on Render. See `render.yaml` for deployment configuration.

## 📝 Example Usage

```
User: "Add a blue cotton t-shirt to my wardrobe"
FitFinder: "I've added a blue cotton t-shirt to your wardrobe! Would you like me to suggest some outfits that would go well with it?"

User: "Create a casual summer outfit using that t-shirt"
FitFinder: "Here's a great casual summer outfit..."
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and formatting
5. Submit a pull request

## 📄 License

MIT
