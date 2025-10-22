#!/usr/bin/env python3
"""Test script to verify Gemini AI insights generation"""

import os
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not set")
    exit(1)

print(f"✓ API Key found")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('models/gemini-2.5-flash-preview-09-2025')
    print("✓ Model initialized: gemini-2.5-flash-preview")

    # Sample airline data
    test_data = """
    Carrier  avg_cost_per_mile  avg_delay_min  delay_rate
    WN       1.16               10.2           0.165
    AA       2.45               15.3           0.189
    DL       2.78               12.1           0.174
    OO       4.34               18.5           0.219
    """

    prompt = """Here is a table of airline performance metrics:

    {test_data}

    Answer these three questions using ONLY the exact numbers shown in the table above:
    1. Which carrier has the lowest avg_cost_per_mile and what is that cost?
    2. Which carrier has the highest avg_delay_min and what is that delay?
    3. Which carrier has the lowest delay_rate and what is that rate?

    Format: Just the facts with numbers, no explanations."""

    # Configure safety settings
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    print("\n📝 Generating AI insights...")
    response = gemini_model.generate_content(
        contents=prompt,
        generation_config={
            'temperature': 0.1,  # More deterministic
            'top_p': 1.0,
            'top_k': 1,
            'max_output_tokens': 256,  # Shorter response
        },
        safety_settings=safety_settings
    )

    # Check response
    if not response.candidates or not response.candidates[0].content.parts:
        print("❌ Response was blocked or empty")
        print(f"Finish reason: {response.candidates[0].finish_reason if response.candidates else 'No candidates'}")
    else:
        print("✓ AI insights generated successfully!")
        print("\n" + "="*60)
        print(response.text)
        print("="*60)

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
