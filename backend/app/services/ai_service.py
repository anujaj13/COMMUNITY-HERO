"""
AI Service — powered by Google Gemini with Structured Outputs
Provides:
  - analyze_issue()   : auto-categorize + estimate priority + generate tags
  - find_duplicates() : detect similar existing issues by description
"""
import os
import json
import re
import time
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from google import genai
from google.genai import types
from app.utils.logging_config import logger

# ── Categories / priorities (must match DB enums) ─────────────
CATEGORIES = [
    "pothole", "water_leak", "streetlight", "waste_management",
    "road_damage", "flooding", "public_facility", "safety", "other"
]
PRIORITIES = ["low", "medium", "high", "critical"]

_client: Optional[genai.Client] = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        logger.info("AiService: Initializing Gemini client...")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("AiService: GEMINI_API_KEY not found in environment!")
            raise RuntimeError("GEMINI_API_KEY environment variable not set")
        _client = genai.Client(api_key=api_key)
    return _client


def _call_gemini_with_retry(call_func, max_retries=3, initial_delay=2):
    """
    Wrapper to retry Gemini API calls with exponential backoff.
    Handles 503 UNAVAILABLE and other transient errors.
    """
    for attempt in range(max_retries + 1):
        try:
            return call_func()
        except Exception as e:
            error_str = str(e).lower()
            is_transient = "503" in error_str or "unavailable" in error_str or "overloaded" in error_str
            
            if not is_transient or attempt >= max_retries:
                raise  # Not transient or last retry, give up
            
            delay = initial_delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"AiService: Transient error on attempt {attempt + 1}/{max_retries + 1}. Retrying in {delay}s... Error: {e}")
            time.sleep(delay)


def _parse_json_block(text: str) -> dict:
    """Extract JSON from a Gemini response."""
    try:
        # Ensure text is a string
        if not isinstance(text, str):
            logger.error(f"AiService: Response is not a string, type={type(text)}, value={text}")
            raise ValueError(f"Response is not a string: {type(text)}")
        
        # First try direct parsing
        data = json.loads(text)
        logger.debug(f"AiService: Parsed JSON directly: {list(data.keys()) if isinstance(data, dict) else 'list'}")
        return data
    except json.JSONDecodeError:
        pass  # Try other methods
    
    try:
        # Try removing markdown code blocks (```json ... ```)
        if "```" in text:
            start = text.find("```")
            end = text.rfind("```")
            if start != -1 and end != -1 and start < end:
                text = text[start+3:end]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
                data = json.loads(text)
                logger.debug(f"AiService: Parsed JSON from markdown block: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                return data
    except Exception as e:
        logger.debug(f"AiService: Markdown extraction failed: {e}")
    
    try:
        # Try using LangChain parser as fallback
        parser = JsonOutputParser()
        data = parser.parse(text)
        logger.debug(f"AiService: Parsed JSON with LangChain: {list(data.keys()) if isinstance(data, dict) else 'list'}")
        return data
    except Exception as e:
        logger.error(f"AiService: Failed to parse JSON from AI response")
        logger.error(f"AiService: Response text length: {len(text) if isinstance(text, str) else 'N/A'}")
        logger.error(f"AiService: Response text (first 300 chars): {str(text)[:300]}")
        raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")


# ── Schemas for Structured Outputs ────────────────────────────
class MultimodalAnalysisResult(BaseModel):
    title: str = Field(description="Short descriptive title, max 10 words")
    category: str = Field(description=f"One of: {', '.join(CATEGORIES)}")
    priority: str = Field(description=f"One of: {', '.join(PRIORITIES)}")
    description: str = Field(description="Detailed professional description of the observed issue, impact, and suggested fix")
    tags: list[str] = Field(description="2 or 3 relevant tags")
    summary: str = Field(description="One sentence summary")

class TextAnalysisResult(BaseModel):
    category: str = Field(description=f"One of: {', '.join(CATEGORIES)}")
    priority: str = Field(description=f"One of: {', '.join(PRIORITIES)}")
    tags: list[str] = Field(description="2 or 3 relevant tags")
    summary: str = Field(description="One sentence plain-English summary of the issue")
    severity_rationale: str = Field(description="One sentence explaining the priority choice")

class DuplicateMatch(BaseModel):
    id: int = Field(description="The ID of the matching issue")
    similarity_score: float = Field(description="A similarity score between 0.0 and 1.0")
    reason: str = Field(description="One sentence reason explaining why it is a duplicate")

class DuplicateCheckResult(BaseModel):
    duplicates: list[DuplicateMatch] = Field(description="List of issues with similarity_score >= 0.6. Empty list if none.")


# ── 1. Analyze a new issue ────────────────────────────────────
def analyze_issue(title: str, description: str) -> dict:
    """Analyze a text-only community issue report."""
    prompt = f"""You are an AI assistant for a community issue-reporting platform.
Analyze the following report and respond with the requested JSON schema structure.

Title: {title}
Description: {description}"""
    return _run_gemini_json(prompt, TextAnalysisResult)


def analyze_multimodal_issue(context: str, file_path: str, mime_type: str) -> dict:
    """
    Analyzes an image or video along with optional user context.
    Returns generated title, category, full description, priority, tags, and summary.
    """
    logger.info(f"AiService: Starting multimodal analysis (path={file_path}, type={mime_type})")
    
    try:
        # Validate file exists and is readable
        if not os.path.exists(file_path):
            logger.error(f"AiService: File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        logger.info(f"AiService: File size: {file_size} bytes")
        
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        
        if not file_bytes:
            logger.error("AiService: File is empty")
            raise ValueError("File is empty")
        
        logger.debug(f"AiService: File read successfully, {len(file_bytes)} bytes")

        prompt = f"""You are an urban maintenance expert. Analyze the attached media (image/video).
User Context: {context if context else "No context provided"}

Generate a complete issue report based on the visual evidence."""

        logger.debug(f"AiService: Getting Gemini client...")
        client = _get_client()
        logger.debug(f"AiService: Client initialized successfully")
        
        logger.debug(f"AiService: Creating content with mime_type={mime_type}")
        content = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    types.Part.from_text(text=prompt)
                ]
            )
        ]
        
        def make_request():
            logger.debug(f"AiService: Sending multimodal request to Gemini (model=gemini-2.5-flash)...")
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=content,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=MultimodalAnalysisResult,
                )
            )
        
        response = _call_gemini_with_retry(make_request, max_retries=3, initial_delay=2)
        
        logger.debug(f"AiService: Received response from Gemini, length={len(response.text)}")
        logger.debug(f"AiService: Response text {response.text}")
        
        result = _parse_json_block(response.text)
        logger.info(f"AiService: Multimodal analysis successful: {result.get('title')}")
        return result
        
    except Exception as e:
        logger.error(f"AiService: Error in multimodal analysis: {type(e).__name__}: {str(e)}", exc_info=True)
        # Return fallback data instead of crashing if possible
        return {
            "title": "Unidentified Issue",
            "category": "other",
            "priority": "medium",
            "description": "The AI service was unable to analyze this issue. Please provide details manually.",
            "tags": ["error"],
            "summary": "AI Analysis failed."
        }


def _run_gemini_json(prompt: str, response_schema=None) -> dict:
    try:
        client = _get_client()
        
        def make_request():
            config_args = {
                "temperature": 0.1,
            }
            if response_schema:
                config_args["response_mime_type"] = "application/json"
                config_args["response_schema"] = response_schema
            else:
                config_args["max_output_tokens"] = 300
                
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(**config_args),
            )
        
        response = _call_gemini_with_retry(make_request, max_retries=3, initial_delay=2)
        result = _parse_json_block(response.text)
        return result
    except Exception as exc:
        logger.error(f"AiService: _run_gemini_json failed after retries: {exc}")
        return {
            "error": str(exc),
            "category": "other",
            "priority": "medium",
            "tags": [],
            "summary": "",
            "severity_rationale": ""
        }


# ── 2. Find duplicate issues ──────────────────────────────────
def find_duplicates(new_title: str, new_description: str, existing_issues: list[dict]) -> list[dict]:
    """
    Given a new issue and a list of existing issues, return those that are
    likely duplicates (same problem at roughly the same location/context).
    
    existing_issues: list of dicts with keys: id, title, description, address, status
    Returns: list of {id, title, similarity_score, reason}
    """
    if not existing_issues:
        return []

    # Build a compact representation of existing issues for the prompt
    issues_text = "\n".join(
        f"[{i['id']}] {i['title']} — {i.get('address','?')} — {(i.get('description') or '')[:100]}"
        for i in existing_issues[:30]   # cap at 30 to stay within token budget
    )

    prompt = f"""You are an AI assistant for a community issue-reporting platform.
A new issue is being submitted. Identify which existing issues (if any) are likely duplicates.

NEW ISSUE:
Title: {new_title}
Description: {new_description}

EXISTING ISSUES (format: [id] title — address — description excerpt):
{issues_text}

Identify duplicates with similarity_score >= 0.6."""

    try:
        client = _get_client()
        
        def make_request():
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=DuplicateCheckResult,
                ),
            )
        
        response = _call_gemini_with_retry(make_request, max_retries=3, initial_delay=2)
        parsed = _parse_json_block(response.text)
        
        # Extract the list of duplicates from the schema result
        matches = parsed.get("duplicates", []) if isinstance(parsed, dict) else []
        
        # Validate entries
        valid = []
        existing_ids = {i["id"] for i in existing_issues}
        for m in matches:
            if isinstance(m, dict) and m.get("id") in existing_ids:
                valid.append({
                    "id": int(m["id"]),
                    "similarity_score": float(m.get("similarity_score", 0.6)),
                    "reason": str(m.get("reason", "")),
                })
        return sorted(valid, key=lambda x: x["similarity_score"], reverse=True)

    except Exception as e:
        logger.warning(f"AiService: find_duplicates failed: {e}")
        return []
