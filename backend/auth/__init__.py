"""
Authentication module for FitFinder
"""

from .chainlit_auth import authenticate_user, add_user, get_current_user, require_admin

__all__ = ['authenticate_user', 'add_user', 'get_current_user', 'require_admin'] 