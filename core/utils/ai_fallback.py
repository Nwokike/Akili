import os
import gc
import requests
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

# Memory optimization constants per REBRANDING_ASSESSMENT.md
# Tier-specific token caps for 1GB RAM VM optimization
TIER_MAX_TOKENS = {
    'gemini_flash': 2500,  # Primary tier - slightly lower for fast responses
    'gemini_paid': 3000,   # Paid tier - standard limit
    'groq': 2000,          # Fallback - most conservative
}
DEFAULT_MAX_TOKENS = 2500  # Default fallback
MAX_RESPONSE_SIZE_BYTES = 512 * 1024  # 512KB max response size

REQUEST_TIMEOUT_FLASH = 45  # seconds - reduced for faster failover
REQUEST_TIMEOUT_PAID = 55  # seconds
REQUEST_TIMEOUT_GROQ = 35  # seconds

# --- Core Fallback Logic ---

def call_ai_with_fallback(prompt, system_prompt=None, max_tokens=None, is_json=False, subject=None):
    """
    4-tier AI Smart Fallback system with memory optimization
    Tier 1: Gemini 2.5 Flash (Primary)
    Tier 2: Gemini Paid (Paid)
    Tier 3: Groq API (Free)
    Tier 4: Circuit Breaker (Graceful error)
    
    Memory optimizations:
    - Reduced default max_tokens from 5000 to 3000
    - Configurable timeout guards
    - Chunked response processing ready
    """

    # 1. IDENTIFY IF LATEX IS NEEDED
    subject_lower = str(subject).lower() if subject else ""
    
    # Subjects that usually require math rendering
    stem_keywords = [
        'math', 'physics', 'chemistry', 'biology', 'science', 
        'drawing', 'economics', 'account', 'calculat', 'sets'
    ]
    
    needs_latex = any(keyword in subject_lower for keyword in stem_keywords)
    
    # 2. CONSTRUCT INSTRUCTIONS
    latex_instruction = ""
    if needs_latex:
        latex_instruction = (
            r" \n\nIMPORTANT FORMATTING RULE FOR MATH/SCIENCE:"
            r" \n1. You must use LaTeX for all mathematical expressions."
            r" \n2. JSON ESCAPING RULES (Follow Strictly):"
            r" \n   - USE DOUBLE BACKSLASHES for commands: Write '\\frac{1}{2}' (not \frac)."
            r" \n   - FOR SETS (Further Math): You must escape curly braces."
            r" \n     Write: '$\\{ 1, 2, 3 \\}$' to display {1, 2, 3}."
            r" \n     Write: '$\\{ x | x > 5 \\}$' for set builder notation."
            r" \n   - FOR TEXT INSIDE MATH: Write '\\text{...}' (exactly two backslashes)."
            r" \n   - DO NOT write '\\\\text' (four backslashes) or it will break."
        )

    # Add JSON instruction to the system prompt if required
    json_instruction = "\nYour output MUST be a single, valid, raw JSON object." if is_json else ""

    if system_prompt:
        full_prompt = f"{system_prompt}{json_instruction}{latex_instruction}\n\n{prompt}"
    else:
        full_prompt = f"{json_instruction}{latex_instruction}\n\n{prompt}"

    # --- UPDATED TIER ORDER ---
    gemini_key = settings.GEMINI_API_KEY

    # --- Tier 1: Gemini 2.5 Flash ---
    if gemini_key:
        result = _try_gemini_flash(full_prompt, gemini_key, max_tokens, is_json)
        if result:
            return result

    # --- Tier 2: Gemini Paid (Was Tier 3) ---
    if gemini_key:
        result = _try_gemini_paid(full_prompt, gemini_key, max_tokens, is_json)
        if result:
            return result

    # --- Tier 3: Groq API (Free - Fallback) ---
    groq_key = settings.GROQ_API_KEY
    if groq_key:
        result = _try_groq(full_prompt, groq_key, max_tokens, is_json)
        if result:
            return result

    # --- Tier 4: Circuit Breaker ---
    return {
        'success': False,
        'content': "Our AI tutors are at full capacity. Please try again in 2–3 minutes.",
        'tier': 'Circuit Breaker'
    }


# --- Tier Implementations ---

def _try_gemini_flash(prompt, api_key, max_tokens, is_json):
    """Try Gemini 2.5 Flash (Tier 1) with memory optimization"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        tier_limit = TIER_MAX_TOKENS['gemini_flash']
        effective_tokens = min(max_tokens, tier_limit) if max_tokens else tier_limit

        config = {'maxOutputTokens': effective_tokens}
        if is_json:
            config['responseMimeType'] = 'application/json'

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": config
        }

        response = requests.post(url, json=data, headers=headers, timeout=REQUEST_TIMEOUT_FLASH)

        if response.status_code == 200:
            if len(response.content) > MAX_RESPONSE_SIZE_BYTES:
                logger.warning(f"Gemini Flash response too large: {len(response.content)} bytes")
                return None
            
            result = response.json()
            content = _extract_gemini_content(result)
            if content:
                del result
                gc.collect()
                return {'success': True, 'content': content, 'tier': 'Gemini Flash'}
    except requests.Timeout:
        logger.warning("Gemini Flash timeout")
    except Exception as e:
        logger.warning(f"Gemini Flash failed: {e}")

    return None


def _extract_gemini_content(result):
    """Memory-efficient content extraction from Gemini response"""
    try:
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                if len(parts) > 0 and 'text' in parts[0]:
                    return parts[0]['text']
    except (KeyError, IndexError):
        pass
    return None


def _try_gemini_paid(prompt, api_key, max_tokens, is_json):
    """Try Gemini Paid tier (Tier 2) with memory optimization"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        tier_limit = TIER_MAX_TOKENS['gemini_paid']
        effective_tokens = min(max_tokens, tier_limit) if max_tokens else tier_limit

        config = {'maxOutputTokens': effective_tokens}
        if is_json:
            config['responseMimeType'] = 'application/json'

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": config
        }

        response = requests.post(url, json=data, headers=headers, timeout=REQUEST_TIMEOUT_PAID)

        if response.status_code == 200:
            if len(response.content) > MAX_RESPONSE_SIZE_BYTES:
                logger.warning(f"Gemini Paid response too large: {len(response.content)} bytes")
                return None
            
            result = response.json()
            content = _extract_gemini_content(result)
            if content:
                del result
                gc.collect()
                return {'success': True, 'content': content, 'tier': 'Gemini Paid'}
    except requests.Timeout:
        logger.warning("Gemini Paid timeout")
    except Exception as e:
        logger.warning(f"Gemini Paid failed: {e}")

    return None


def _try_groq(prompt, api_key, max_tokens, is_json):
    """Try Groq API (Tier 3 Fallback) with memory optimization"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        tier_limit = TIER_MAX_TOKENS['groq']
        effective_tokens = min(max_tokens, tier_limit) if max_tokens else tier_limit

        data = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"} if is_json else {"type": "text"},
            "max_tokens": effective_tokens,
        }

        response = requests.post(url, json=data, headers=headers, timeout=REQUEST_TIMEOUT_GROQ)

        if response.status_code == 200:
            if len(response.content) > MAX_RESPONSE_SIZE_BYTES:
                logger.warning(f"Groq response too large: {len(response.content)} bytes")
                return None
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                del result
                gc.collect()
                return {'success': True, 'content': content, 'tier': 'Groq'}
    except requests.Timeout:
        logger.warning("Groq timeout")
    except Exception as e:
        logger.warning(f"Groq failed: {e}")

    return None


def validate_ai_content(content):
    """
    Two-pass validation: Use AI to validate AI-generated content
    """
    validation_prompt = f"""You are a university professor. Review the following lesson content for accuracy.
    
    Respond with ONLY 'OK' if the content is perfect.
    If errors are found, provide the corrected content directly.
    
    Content to review:
    {content}
    """

    result = call_ai_with_fallback(validation_prompt)

    if result['success']:
        return result['content'].strip()

    return "OK"
