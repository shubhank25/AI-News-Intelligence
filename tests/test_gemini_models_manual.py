"""
Purpose:
This file lists Gemini models accessible through the configured API key.

It helps identify models that support content generation before
configuring the application to use one of them.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

print("\nAvailable Gemini models supporting generateContent:\n")

for model in client.models.list():
    supported_methods = getattr(model, "supported_actions", [])

    if "generateContent" in supported_methods:
        print(model.name)
