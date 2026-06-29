#!/usr/bin/env python3
"""
Direct Gemini API test - debug AI analysis issues
Run from backend folder: python test_gemini_direct.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your-api-key-here":
    print("❌ GEMINI_API_KEY not set or is placeholder")
    print("   Fix: Set GEMINI_API_KEY in .env file")
    sys.exit(1)

print(f"✅ API Key found: {api_key[:10]}...")
print()

# Test 1: Simple text analysis
print("=" * 60)
print("TEST 1: Simple Text Analysis")
print("=" * 60)

try:
    from google import genai
    
    client = genai.Client(api_key=api_key)
    print("✅ Gemini client initialized")
    
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Say hello in JSON format: {\"greeting\": \"...\"}",
        config={"temperature": 0.1, "max_output_tokens": 50}
    )
    
    print(f"✅ Text analysis working")
    print(f"Response: {response.text[:100]}")
    print()
    
except Exception as e:
    print(f"❌ Text analysis failed: {e}")
    sys.exit(1)

# Test 2: Image analysis with a small test image
print("=" * 60)
print("TEST 2: Image Analysis (using a test image)")
print("=" * 60)

try:
    import json
    
    # Create a simple test image (1x1 red pixel PNG)
    import base64
    
    # 1x1 red pixel as base64
    red_pixel_base64 = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    
    image_bytes = base64.b64decode(red_pixel_base64)
    
    print(f"Test image size: {len(image_bytes)} bytes")
    
    from google.genai import types
    
    content = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                types.Part.from_text(text="Describe this image briefly in JSON: {\"description\": \"...\"}")
            ]
        )
    ]
    
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=content,
        config={"temperature": 0.1, "max_output_tokens": 100}
    )
    
    print(f"✅ Image analysis working")
    print(f"Response: {response.text[:150]}")
    print()
    
except Exception as e:
    print(f"❌ Image analysis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test JSON parsing
print("=" * 60)
print("TEST 3: JSON Parsing of Response")
print("=" * 60)

try:
    import json
    from langchain_core.output_parsers import JsonOutputParser
    
    test_response = '''```json
{
  "title": "Test Title",
  "category": "pothole",
  "priority": "medium"
}
```'''
    
    # Try direct parsing
    try:
        data = json.loads(test_response)
        print("✅ Direct JSON parsing works")
    except:
        # Try markdown extraction
        if "```" in test_response:
            start = test_response.find("```")
            end = test_response.rfind("```")
            extracted = test_response[start+3:end]
            if extracted.startswith("json"):
                extracted = extracted[4:]
            extracted = extracted.strip()
            data = json.loads(extracted)
            print("✅ Markdown JSON extraction works")
    
    print(f"   Parsed: {data}")
    print()
    
except Exception as e:
    print(f"❌ JSON parsing failed: {e}")
    sys.exit(1)

print("=" * 60)
print("✅ ALL TESTS PASSED - Gemini API is working!")
print("=" * 60)
print()
print("Next steps:")
print("1. Restart backend: Ctrl+C then run: uvicorn app.main:app --reload")
print("2. Try uploading an image in the browser")
print("3. Check backend console for detailed logs")
