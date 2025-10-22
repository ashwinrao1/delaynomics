#!/usr/bin/env python3
"""Test script to list available Gemini models"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not set")
    exit(1)

print(f"✓ API Key found: {GEMINI_API_KEY[:10]}...")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✓ API configured successfully")

    print("\n📋 Available models:")
    print("-" * 60)

    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✓ {model.name}")
            print(f"  Description: {model.description}")
            print(f"  Methods: {', '.join(model.supported_generation_methods)}")
            print()

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
