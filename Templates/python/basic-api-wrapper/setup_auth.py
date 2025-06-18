#!/usr/bin/env python3

import keyring
import getpass
from config import Config

def setup_authentication():
    """Setup secure authentication for the MCP server."""
    print("🔐 Basic API Wrapper MCP Server - Authentication Setup")
    print("=" * 50)
    
    print(f"\nThis will store your API token securely in the system keyring.")
    print(f"Service: {Config.KEYRING_SERVICE}")
    print(f"Username: {Config.KEYRING_USERNAME}")
    
    # Get API token from user
    api_token = getpass.getpass("\nEnter your API token: ").strip()
    
    if not api_token:
        print("❌ API token cannot be empty.")
        return False
    
    try:
        # Store in keyring
        keyring.set_password(Config.KEYRING_SERVICE, Config.KEYRING_USERNAME, api_token)
        print("✅ API token stored securely in keyring.")
        
        # Verify storage
        stored_token = keyring.get_password(Config.KEYRING_SERVICE, Config.KEYRING_USERNAME)
        if stored_token == api_token:
            print("✅ Token verification successful.")
            return True
        else:
            print("❌ Token verification failed.")
            return False
            
    except Exception as e:
        print(f"❌ Error storing token: {e}")
        return False

def remove_authentication():
    """Remove stored authentication."""
    try:
        keyring.delete_password(Config.KEYRING_SERVICE, Config.KEYRING_USERNAME)
        print("✅ Authentication removed successfully.")
    except keyring.errors.PasswordDeleteError:
        print("ℹ️ No authentication found to remove.")
    except Exception as e:
        print(f"❌ Error removing authentication: {e}")

def check_authentication():
    """Check if authentication is properly configured."""
    try:
        token = keyring.get_password(Config.KEYRING_SERVICE, Config.KEYRING_USERNAME)
        if token:
            print("✅ Authentication is configured.")
            return True
        else:
            print("❌ No authentication found.")
            return False
    except Exception as e:
        print(f"❌ Error checking authentication: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "setup":
            setup_authentication()
        elif command == "remove":
            remove_authentication()
        elif command == "check":
            check_authentication()
        else:
            print("Usage: python setup_auth.py [setup|remove|check]")
    else:
        setup_authentication() 