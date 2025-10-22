#!/usr/bin/env python3
"""Debug script to see what's happening with AI response"""

import os
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Load actual data
airline_df = pd.read_csv('outputs/airline_summary.csv')

try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')

    # Use the EXACT same logic as in the dashboard
    top_5 = airline_df.nsmallest(5, 'avg_cost_per_mile')[['Carrier', 'avg_cost_per_mile', 'avg_delay_min', 'delay_rate']].to_string(index=False)
    worst_3 = airline_df.nlargest(3, 'avg_cost_per_mile')[['Carrier', 'avg_cost_per_mile', 'avg_delay_min', 'delay_rate']].to_string(index=False)

    prompt = f"""
    Analyze this airline delay performance data and provide exactly 3 key insights for travelers:

    TOP 5 BEST PERFORMERS (by cost per mile):
    {top_5}

    WORST 3 PERFORMERS:
    {worst_3}

    Format your response as:
    1. **Best Performer**: [1-2 sentences with specific numbers]
    2. **Worst Performer**: [1-2 sentences with specific numbers]
    3. **Surprising Pattern**: [1-2 sentences about an interesting trend or recommendation]

    Be concise, specific, and actionable. Use the actual carrier codes and numbers from the data.
    """

    print("=" * 60)
    print("PROMPT:")
    print(prompt)
    print("=" * 60)

    # Configure safety settings
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    response = gemini_model.generate_content(
        prompt,
        generation_config={
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 1024,
        },
        safety_settings=safety_settings
    )

    print("\n" + "=" * 60)
    print("RESPONSE OBJECT:")
    print(f"Has candidates: {bool(response.candidates)}")
    if response.candidates:
        candidate = response.candidates[0]
        print(f"Finish reason: {candidate.finish_reason}")
        print(f"Has content: {bool(candidate.content)}")
        print(f"Has parts: {bool(candidate.content.parts)}")
        if candidate.content.parts:
            print(f"Number of parts: {len(candidate.content.parts)}")
        print(f"Safety ratings: {candidate.safety_ratings}")
    print("=" * 60)

    # Check if response was blocked or has no text
    if not response.candidates or not response.candidates[0].content.parts:
        print("\n❌ Response was blocked or empty")
    else:
        print("\n✓ Response generated successfully!")
        print("\n" + "=" * 60)
        print("RESPONSE TEXT:")
        print(response.text)
        print("=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
