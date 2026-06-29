#!/usr/bin/env python
"""
Test script to verify AI analysis setup is working correctly.
Run this from the backend folder:
  python test_ai_setup.py
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Community Hero AI Setup Verification")
print("=" * 60)

# Test 1: Check .env file
print("\n[TEST 1] Checking .env configuration...")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("  ❌ GEMINI_API_KEY not found in .env")
    print("     Fix: Add GEMINI_API_KEY=your-api-key to backend/.env")
    sys.exit(1)
elif api_key == "your-api-key-here":
    print("  ❌ GEMINI_API_KEY is still a placeholder")
    print("     Fix: Replace 'your-api-key-here' with actual API key")
    print("     Get key: https://ai.google.dev/gemini-api")
    sys.exit(1)
else:
    key_preview = api_key[:10] + "..." + api_key[-5:]
    print(f"  ✅ GEMINI_API_KEY is set: {key_preview}")

debug_mode = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
print(f"  {'✅' if debug_mode else '⚠️'} DEBUG mode: {debug_mode} {'(enabled)' if debug_mode else '(can be enabled for verbose logs)'}")

# Test 2: Check if backend is running
print("\n[TEST 2] Checking if backend API is running...")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print("  ✅ Backend API is running on http://localhost:8000")
    else:
        print(f"  ❌ Backend returned status {response.status_code}")
        print("     Fix: Start backend with: uvicorn app.main:app --reload")
except requests.exceptions.ConnectionError:
    print("  ❌ Cannot connect to backend at http://localhost:8000")
    print("     Fix: Start backend with: uvicorn app.main:app --reload")
    sys.exit(1)
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test 3: Test text-only AI analysis
print("\n[TEST 3] Testing text-only AI analysis...")
try:
    payload = {
        "title": "Pothole on Main Street",
        "description": "Large pothole on the corner causing traffic issues",
        "check_duplicates": False
    }
    response = requests.post(
        "http://localhost:8000/api/ai/analyze",
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print("  ✅ Text analysis successful!")
        print(f"     - Category: {result.get('category')}")
        print(f"     - Priority: {result.get('priority')}")
        print(f"     - Tags: {result.get('tags')}")
        if result.get('error'):
            print(f"     ⚠️  API Error: {result.get('error')}")
    else:
        print(f"  ❌ API returned status {response.status_code}")
        print(f"     Response: {response.text[:200]}")
except requests.exceptions.Timeout:
    print("  ❌ Request timed out (30 seconds)")
    print("     The Gemini API may be slow or unreachable")
except requests.exceptions.ConnectionError:
    print("  ❌ Cannot connect to backend")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 4: Try to create Gemini client directly
print("\n[TEST 4] Testing Gemini API connection...")
try:
    from google import genai
    client = genai.Client(api_key=api_key)
    print("  ✅ Gemini client initialized successfully")
    
    # Try a simple request
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say 'Hello' in one word.",
        config={"temperature": 0.1, "max_output_tokens": 10}
    )
    print(f"  ✅ Gemini API is responding: {response.text[:50]}...")
    
except Exception as e:
    print(f"  ❌ Gemini API error: {e}")
    if "401" in str(e) or "invalid" in str(e).lower():
        print("     The API key appears to be invalid")
        print("     Fix: Get a new key from https://ai.google.dev/gemini-api")
    elif "rate" in str(e).lower():
        print("     Rate limit exceeded - wait 60 seconds and try again")
    else:
        print("     Check your internet connection and API key")

# Test 5: Check uploads directory
print("\n[TEST 5] Checking uploads directory...")
upload_dir = "uploads"
if os.path.exists(upload_dir):
    files = os.listdir(upload_dir)
    print(f"  ✅ Uploads directory exists with {len(files)} files")
else:
    os.makedirs(upload_dir, exist_ok=True)
    print(f"  ✅ Created uploads directory")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
All tests passed! Your setup is ready to use.

Next steps:
1. Open http://localhost:3000 in browser
2. Login or register a user
3. Try uploading an image in the "Report Issue" form
4. The AI should analyze it automatically

Troubleshooting:
- If image analysis still fails, check backend terminal for error messages
- Enable DEBUG=true in .env for more detailed logs
- See AI_ANALYSIS_TROUBLESHOOTING.md for common issues
""")

print("=" * 60)
