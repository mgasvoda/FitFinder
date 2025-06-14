#!/usr/bin/env python3
"""
User Management Utility for FitFinder Chainlit Authentication

This script allows you to add, remove, and list users for the Chainlit interface.
"""

import argparse
import getpass
import sys
from typing import Dict, Any
from backend.auth.chainlit_auth import USERS, add_user, hash_password

def list_users():
    """List all users in the system"""
    print("\n📋 **Current Users:**")
    print("=" * 50)
    
    if not USERS:
        print("No users found.")
        return
    
    for username, user_data in USERS.items():
        print(f"👤 **{username}**")
        print(f"   Name: {user_data.get('name', 'N/A')}")
        print(f"   Role: {user_data.get('role', 'user')}")
        print()

def add_user_interactive():
    """Interactively add a new user"""
    print("\n➕ **Add New User**")
    print("=" * 30)
    
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty.")
        return False
    
    if username in USERS:
        print(f"❌ User '{username}' already exists.")
        return False
    
    name = input("Enter full name (optional): ").strip()
    
    role = input("Enter role (user/admin) [user]: ").strip().lower()
    if role not in ['user', 'admin']:
        role = 'user'
    
    password = getpass.getpass("Enter password: ")
    if not password:
        print("❌ Password cannot be empty.")
        return False
    
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords do not match.")
        return False
    
    # Add the user
    success = add_user(username, password, name or None, role)
    if success:
        print(f"✅ User '{username}' added successfully!")
        return True
    else:
        print(f"❌ Failed to add user '{username}'.")
        return False

def remove_user_interactive():
    """Interactively remove a user"""
    print("\n🗑️ **Remove User**")
    print("=" * 25)
    
    if not USERS:
        print("No users to remove.")
        return False
    
    list_users()
    username = input("Enter username to remove: ").strip()
    
    if not username:
        print("❌ Username cannot be empty.")
        return False
    
    if username not in USERS:
        print(f"❌ User '{username}' not found.")
        return False
    
    confirm = input(f"Are you sure you want to remove user '{username}'? (yes/no): ").strip().lower()
    if confirm in ['yes', 'y']:
        del USERS[username]
        print(f"✅ User '{username}' removed successfully!")
        return True
    else:
        print("❌ Operation cancelled.")
        return False

def change_password_interactive():
    """Interactively change a user's password"""
    print("\n🔑 **Change Password**")
    print("=" * 30)
    
    if not USERS:
        print("No users found.")
        return False
    
    list_users()
    username = input("Enter username: ").strip()
    
    if not username:
        print("❌ Username cannot be empty.")
        return False
    
    if username not in USERS:
        print(f"❌ User '{username}' not found.")
        return False
    
    password = getpass.getpass("Enter new password: ")
    if not password:
        print("❌ Password cannot be empty.")
        return False
    
    password_confirm = getpass.getpass("Confirm new password: ")
    if password != password_confirm:
        print("❌ Passwords do not match.")
        return False
    
    USERS[username]["password_hash"] = hash_password(password)
    print(f"✅ Password for user '{username}' changed successfully!")
    return True

def main():
    """Main function for the user management utility"""
    parser = argparse.ArgumentParser(
        description="FitFinder User Management Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backend.auth.user_manager --list
  python -m backend.auth.user_manager --add
  python -m backend.auth.user_manager --remove
  python -m backend.auth.user_manager --change-password
        """
    )
    
    parser.add_argument("--list", "-l", action="store_true", help="List all users")
    parser.add_argument("--add", "-a", action="store_true", help="Add a new user")
    parser.add_argument("--remove", "-r", action="store_true", help="Remove a user")
    parser.add_argument("--change-password", "-p", action="store_true", help="Change user password")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        # No arguments provided, show interactive menu
        print("🔐 **FitFinder User Management**")
        print("=" * 40)
        print("1. List users")
        print("2. Add user")
        print("3. Remove user")
        print("4. Change password")
        print("5. Exit")
        
        while True:
            try:
                choice = input("\nSelect an option (1-5): ").strip()
                
                if choice == '1':
                    list_users()
                elif choice == '2':
                    add_user_interactive()
                elif choice == '3':
                    remove_user_interactive()
                elif choice == '4':
                    change_password_interactive()
                elif choice == '5':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
    else:
        # Handle command line arguments
        if args.list:
            list_users()
        elif args.add:
            add_user_interactive()
        elif args.remove:
            remove_user_interactive()
        elif args.change_password:
            change_password_interactive()

if __name__ == "__main__":
    main() 