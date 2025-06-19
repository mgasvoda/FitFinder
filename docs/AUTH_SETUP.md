# FitFinder Authentication Setup Guide

This document explains how to set up and use the user authentication system for the Chainlit chat interface.

## 🔐 Authentication Overview

FitFinder uses **Chainlit User/Password Authentication** for web browser access to the chat interface.

## 🚀 Quick Setup

### 1. Environment Variables

Create a `.env` file in the project root with your authentication settings:

```bash
# Chainlit Authentication
CHAINLIT_AUTH_SECRET=your-chainlit-secret-key-here
CHAINLIT_ADMIN_USERNAME=admin
CHAINLIT_ADMIN_PASSWORD=your-secure-password-here

# AI Service API Key
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### 2. Default Credentials

If you don't set environment variables, the system uses these defaults:

- **Chainlit Username**: `admin`
- **Chainlit Password**: `fitfinder2024!`

⚠️ **IMPORTANT**: Change these defaults in production!

## 👤 Chainlit User Authentication

### Default Login

When you first access the Chainlit interface, use:

- **Username**: `admin` (or your `CHAINLIT_ADMIN_USERNAME`)
- **Password**: `fitfinder2024!` (or your `CHAINLIT_ADMIN_PASSWORD`)

### Managing Users

Use the built-in user management utility:

```bash
# Interactive user management
python -m backend.auth.user_manager

# Or use command line options
python -m backend.auth.user_manager --list
python -m backend.auth.user_manager --add
python -m backend.auth.user_manager --remove
python -m backend.auth.user_manager --change-password
```

### Adding New Users

1. **Via User Manager**:
   ```bash
   python -m backend.auth.user_manager --add
   ```

2. **Programmatically**:
   ```python
   from backend.auth import add_user
   
   success = add_user(
       username="john_doe",
       password="secure_password",
       name="John Doe",
       role="user"  # or "admin"
   )
   ```

### User Roles

- **admin**: Full access to all features
- **user**: Standard access (you can customize permissions)

## 🛠️ Running the Service

### Start Chainlit Chat Interface

```bash
chainlit run backend/chainlit_app.py --port 8001
```

The interface will be available at `http://localhost:8001`

## 🔧 Configuration

### Chainlit Configuration

Chainlit auth is configured in `.chainlit/config.toml`:

```toml
[auth]
require_login = true
```

### Environment Configuration

All settings are managed through environment variables in your `.env` file:

```bash
# Required: Admin user credentials
CHAINLIT_ADMIN_USERNAME=admin
CHAINLIT_ADMIN_PASSWORD=your-secure-password

# Required: AI service API key
ANTHROPIC_API_KEY=your-anthropic-key

# Optional: Custom auth secret
CHAINLIT_AUTH_SECRET=your-secret-key

# Optional: Database location
DATABASE_URL=sqlite:///./fitfinder.db
```

## 🚦 Security Considerations

### Production Deployment

1. **Change Default Credentials**: Never use default passwords in production
2. **Strong Passwords**: Use complex passwords for all user accounts
3. **Environment Variables**: Store all secrets in environment variables, not code
4. **HTTPS**: Always use HTTPS in production
5. **Rate Limiting**: Consider adding rate limiting to prevent abuse

### Generating Secure Keys

```python
import secrets

# Generate a secure auth secret
auth_secret = secrets.token_urlsafe(32)
print(f"Auth Secret: {auth_secret}")

# Generate a secure password
password = secrets.token_urlsafe(16)
print(f"Secure Password: {password}")
```

## 🐛 Troubleshooting

### Common Issues

1. **Chainlit login not working**
   - Verify authentication is enabled in `.chainlit/config.toml`
   - Check that the auth module is properly imported
   - Verify your username/password are correct

2. **Environment variables not loading**
   - Make sure your `.env` file is in the project root
   - Verify environment variable names match exactly

3. **"Missing ANTHROPIC_API_KEY" error**
   - Add your Anthropic API key to the `.env` file
   - Get your API key from https://console.anthropic.com/

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Updates and Migration

When updating the authentication system:

1. Back up your user data
2. Update environment variables if needed
3. Test authentication with the new system
4. Use the user management utility to debug user issues

## 📞 Support

If you encounter issues with authentication:

1. Check the logs for detailed error messages
2. Verify your environment variables
3. Test with the default credentials first
4. Use the user management utility to debug user issues

Remember to never commit sensitive credentials to version control! 