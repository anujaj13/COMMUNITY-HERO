# Gemini API Setup Guide

The Community Hero platform includes AI-powered image analysis to automatically categorize and analyze community issues. This requires a Google Gemini API key.

## Getting Your Gemini API Key

1. **Go to Google AI Studio**: https://ai.google.dev/gemini-api
2. **Sign in** with your Google account (free)
3. **Click "Get API Key"** in the top left
4. **Create a new API key** (or use existing project)
5. **Copy the API key** to your clipboard

## Setup Steps

### Option 1: Automatic (Recommended for Development)

The `.env` file in the `backend/` folder should already have a placeholder:

```env
GEMINI_API_KEY=your-api-key-here
```

**Replace `your-api-key-here` with your actual API key** from step 1 above.

### Option 2: Environment Variable

If using Docker or production:

```bash
export GEMINI_API_KEY=your-api-key-here
```

Or in Windows PowerShell:
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

## Verify It Works

1. Start the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/Scripts/activate  # Windows: call venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd frontend
   python -m http.server 3000
   ```

3. Upload an image in the "Report Issue" form
4. The AI should analyze it and auto-fill the category and priority
5. You should see success logs in the backend terminal

## Troubleshooting

### "Unidentified Issue" Error

If you see "The AI service was unable to analyze this issue" message:

1. **Check the backend logs** - Look for error messages like:
   ```
   AiService: Error in multimodal analysis: ...
   ```

2. **Common issues**:
   - ❌ API key not set → Check `.env` file has `GEMINI_API_KEY=your-actual-key`
   - ❌ API key invalid → Get a new key from https://ai.google.dev/gemini-api
   - ❌ API quota exceeded → Wait 60 seconds or create new API key
   - ❌ Image format not supported → Use JPG, PNG, or GIF (not WebP)
   - ❌ Image too large → Keep under 20MB

3. **Check backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"ok"}`

4. **Test AI directly**:
   ```bash
   curl -X POST http://localhost:8000/api/ai/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Pothole on Main Street",
       "description": "Large pothole causing problems",
       "check_duplicates": false
     }'
   ```
   Should return JSON with category, priority, tags, etc.

## API Limits

- **Free Tier**: 
  - 60 requests per minute
  - 1,500 requests per day
- **Paid Tier**: Higher limits available

If you hit rate limits, the fallback response is returned and the issue is created manually.

## Model Information

The platform uses:
- **Primary Model**: `gemini-2.0-flash` - Fast image analysis
- **Fallback**: Text-only analysis if image fails

Both support multimodal analysis (text + image/video).

## Privacy & Security

- 🔒 Images are only sent to Google Gemini API
- 🔒 Stored in your database locally
- 🔒 No images are shared with third parties
- 🔒 API key is stored in `.env` (never commit this!)

## Documentation

- Gemini API Docs: https://ai.google.dev/docs
- Supported Formats: https://ai.google.dev/gemini-api/docs/vision

## Need Help?

1. Check backend logs: `uvicorn` terminal output
2. Enable debug mode in `.env`: `DEBUG=true`
3. Review the AI service code: `backend/app/services/ai_service.py`

---

**Note**: The GEMINI_API_KEY in `.env` is for development/testing. For production, use environment variables or secrets management (AWS Secrets Manager, Azure Key Vault, etc.).
