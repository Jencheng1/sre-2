#!/usr/bin/env python3
"""
User management script for SRE Copilot authentication.
"""

import sys
import getpass
from auth_config import add_user, delete_user, change_password, list_users

def print_menu():
    """Print the main menu."""
    print("\n=== SRE Copilot User Management ===")
    print("1. List users")
    print("2. Add user")
    print("3. Change password")
    print("4. Delete user")
    print("5. Exit")
    print("==================================")

def handle_list_users():
    """List all users."""
    print("\nCurrent users:")
    users = list_users()
    if users:
        print(f"{'Username':<20} {'Role':<15} {'Created':<30}")
        print("-" * 65)
        for username, role, created in users:
            print(f"{username:<20} {role:<15} {created:<30}")
    else:
        print("No users found.")

def handle_add_user():
    """Add a new user."""
    print("\nAdd new user:")
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return
    
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        print("Passwords do not match.")
        return
    
    if len(password) < 8:
        print("Password must be at least 8 characters long.")
        return
    
    role = input("Role (admin/viewer) [viewer]: ").strip() or "viewer"
    if role not in ["admin", "viewer"]:
        print("Invalid role. Must be 'admin' or 'viewer'.")
        return
    
    success, message = add_user(username, password, role)
    print(message)

def handle_change_password():
    """Change a user's password."""
    print("\nChange password:")
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return
    
    old_password = getpass.getpass("Current password: ")
    new_password = getpass.getpass("New password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    
    if new_password != confirm_password:
        print("Passwords do not match.")
        return
    
    if len(new_password) < 8:
        print("Password must be at least 8 characters long.")
        return
    
    success, message = change_password(username, old_password, new_password)
    print(message)

def handle_delete_user():
    """Delete a user."""
    print("\nDelete user:")
    username = input("Username to delete: ").strip()
    if not username:
        print("Username cannot be empty.")
        return
    
    confirm = input(f"Are you sure you want to delete user '{username}'? (yes/no): ").strip().lower()
    if confirm == "yes":
        success, message = delete_user(username)
        print(message)
    else:
        print("Deletion cancelled.")

def main():
    """Main menu loop."""
    while True:
        print_menu()
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            handle_list_users()
        elif choice == "2":
            handle_add_user()
        elif choice == "3":
            handle_change_password()
        elif choice == "4":
            handle_delete_user()
        elif choice == "5":
            print("\nExiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    print("SRE Copilot User Management Utility")
    print("===================================")
    main()