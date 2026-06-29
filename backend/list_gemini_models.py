#!/usr/bin/env python3
"""
List available Gemini models
Run from backend folder: python list_gemini_models.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not set")
    sys.exit(1)

print(f"API Key: {api_key[:10]}...")
print()

try:
    from google import genai
    
    client = genai.Client(api_key=api_key)
    
    print("Fetching available models...")
    print("=" * 60)
    
    # List all available models
    models = client.models.list()
    
    print(f"Found {len(models)} models:")
    print()
    
    text_models = []
    vision_models = []
    
    for model in models:
        model_name = model.name
        # Extract just the model ID (after models/)
        model_id = model_name.split("/")[-1] if "/" in model_name else model_name
        
        # Check capabilities
        supported_methods = []
        if hasattr(model, 'supported_generation_methods'):
            supported_methods = model.supported_generation_methods
        
        # Categorize
        if 'generateContent' in supported_methods:
            if 'vision' in model_id.lower() or any(x in model_id.lower() for x in ['vision', 'sight']):
                vision_models.append((model_id, supported_methods))
            else:
                text_models.append((model_id, supported_methods))
    
    print("📝 TEXT MODELS:")
    for model_id, methods in text_models:
        print(f"  ✓ {model_id}")
        if methods:
            print(f"    Methods: {', '.join(methods)}")
    
    print()
    print("🖼️ VISION MODELS (for image analysis):")
    for model_id, methods in vision_models:
        print(f"  ✓ {model_id}")
        if methods:
            print(f"    Methods: {', '.join(methods)}")
    
    print()
    print("=" * 60)
    
    # Find recommended models
    recommended_text = None
    recommended_vision = None
    
    # Prefer latest flash models
    for model_id, _ in text_models:
        if 'flash' in model_id.lower():
            recommended_text = model_id
            break
    
    for model_id, _ in vision_models:
        if 'flash' in model_id.lower():
            recommended_vision = model_id
            break
    
    if not recommended_text and text_models:
        recommended_text = text_models[0][0]
    
    if not recommended_vision and vision_models:
        recommended_vision = vision_models[0][0]
    
    print()
    print("RECOMMENDATIONS:")
    if recommended_text:
        print(f"  Text analysis: {recommended_text}")
    if recommended_vision:
        print(f"  Image analysis: {recommended_vision}")
    
    print()
    print("Update backend/app/services/ai_service.py to use these model names.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
