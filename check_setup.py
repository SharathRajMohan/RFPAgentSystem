#!/usr/bin/env python3
"""
Quick setup helper for the RFP Analysis System.
Validates dependencies and OpenAI configuration before running.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


def check_dependencies():
    """Check if required packages are installed."""
    print("Checking dependencies...")
    required = ["fastapi", "uvicorn", "pydantic", "openai", "langgraph"]

    for pkg in required:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} NOT FOUND")
            return False

    print("  All dependencies found!\n")
    return True


def check_openai_key():
    """Check if OpenAI API key is set."""
    print("Checking OpenAI API key...")

    if os.getenv("OPENAI_API_KEY"):
        key = os.getenv("OPENAI_API_KEY")
        masked_key = key[:10] + "..." + key[-5:] if len(key) > 15 else "***"
        print(f"  ✓ OPENAI_API_KEY is set: {masked_key}\n")
        return True
    else:
        print("  ✗ OPENAI_API_KEY environment variable NOT SET\n")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("RFP Analysis System - Setup Check")
    print("=" * 60 + "\n")

    deps_ok = check_dependencies()
    key_ok = check_openai_key()

    if not deps_ok or not key_ok:
        print("=" * 60)
        print("Setup incomplete. Please fix the issues above.")
        print("=" * 60)
        return False

    print("=" * 60)
    print("Setup complete! You can now run:")
    print()
    print("  uv run python -m uvicorn main:app --reload")
    print()
    print("Then visit http://localhost:8000/docs to test the API")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
