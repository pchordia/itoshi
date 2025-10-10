#!/usr/bin/env python3
"""
Secure configuration manager for API keys
Uses macOS Keychain for secure storage
"""

import os
import sys
import subprocess
import json
from typing import Optional

class SecureConfig:
    """Manages API keys securely using macOS Keychain"""
    
    SERVICE_NAME = "AnimeVideoGenerator"
    
    @staticmethod
    def store_key(key_name: str, key_value: str) -> bool:
        """Store an API key in macOS Keychain"""
        try:
            # Use macOS security command to store in keychain
            cmd = [
                'security', 'add-generic-password',
                '-a', os.getlogin(),
                '-s', f"{SecureConfig.SERVICE_NAME}_{key_name}",
                '-w', key_value,
                '-U'  # Update if exists
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Error storing key: {e}")
            return False
    
    @staticmethod
    def get_key(key_name: str) -> Optional[str]:
        """Retrieve an API key from macOS Keychain"""
        try:
            cmd = [
                'security', 'find-generic-password',
                '-a', os.getlogin(),
                '-s', f"{SecureConfig.SERVICE_NAME}_{key_name}",
                '-w'  # Output password only
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # Key not found, try .env fallback
            return SecureConfig._get_from_env(key_name)
        except Exception as e:
            print(f"Error retrieving key: {e}")
            return None
    
    @staticmethod
    def _get_from_env(key_name: str) -> Optional[str]:
        """Fallback: get from .env file"""
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv(key_name)
    
    @staticmethod
    def delete_key(key_name: str) -> bool:
        """Delete an API key from macOS Keychain"""
        try:
            cmd = [
                'security', 'delete-generic-password',
                '-a', os.getlogin(),
                '-s', f"{SecureConfig.SERVICE_NAME}_{key_name}"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Error deleting key: {e}")
            return False
    
    @staticmethod
    def setup_keys_interactive():
        """Interactive setup for first-time users"""
        print("=" * 60)
        print("🔐 Anime Video Generator - API Key Setup")
        print("=" * 60)
        print("\nYour API keys will be stored securely in macOS Keychain.")
        print("They will never be saved in plain text files.\n")
        
        keys = {
            "OPENAI_API_KEY": "OpenAI API Key (for GPT-5 and gpt-image)",
            "GOOGLE_API_KEY": "Google API Key (for Veo 3)",
            "KLING_ACCESS_KEY": "Kling Access Key",
            "KLING_SECRET_KEY": "Kling Secret Key"
        }
        
        for key_name, description in keys.items():
            print(f"\n{description}:")
            # Check if already exists
            existing = SecureConfig.get_key(key_name)
            if existing:
                print(f"  ✓ Already configured (starts with: {existing[:8]}...)")
                update = input("  Update? (y/n): ").strip().lower()
                if update != 'y':
                    continue
            
            key_value = input(f"  Enter {key_name}: ").strip()
            if key_value:
                if SecureConfig.store_key(key_name, key_value):
                    print(f"  ✓ Saved securely to Keychain")
                else:
                    print(f"  ✗ Failed to save")
        
        print("\n" + "=" * 60)
        print("✅ Setup complete! Your keys are stored securely.")
        print("=" * 60)

def main():
    """Run interactive key setup"""
    SecureConfig.setup_keys_interactive()

if __name__ == "__main__":
    main()





