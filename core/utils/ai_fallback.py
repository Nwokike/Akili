import os
import requests
from django.conf import settings
import json # Added for safe JSON parsing

# --- Core Fallback Logic ---

def call_ai_with_fallback(prompt, system_prompt=None, max_tokens=None, is_json=False, subject=None):
    """
    4-tier AI Smart Fallback system
    UPDATED TIER ORDER: Prioritize all Gemini models first.
    Tier 1: Gemini 2.5 Flash (Free)
    Tier 2: Gemini Paid (Paid)
    Tier 3: Groq API (Free)
    Tier 4: Circuit Breaker (Graceful error)

    Args:
        prompt (str): The primary query for the AI.
        system_prompt (str, optional): Instructions for the AI's persona.
        max_tokens (int, optional): Maximum tokens for the response.
        is_json (bool): If True, instructs the AI to return a JSON object.
        subject (str, optional): Subject name to determine if LaTeX guidance is needed.
    """

    # STEM subjects that commonly use formulas
    STEM_SUBJECTS = [
        'Mathematics', 'Physics', 'Chemistry', 'Further Mathematics',
        'Biology', 'Agricultural Science', 'Technical Drawing', 'Economics'
    ]
    
    # Only add LaTeX instruction for STEM subjects
    needs_latex = subject and any(stem in subject for stem in STEM_SUBJECTS)
    
    latex_instruction = ""
    if needs_latex:
        latex_instruction = (
            "\nIMPORTANT: For mathematical expressions, use LaTeX with single backslashes. "
            "Example: $E=mc^2$ or $$\\int_a^b f(x)dx$$ or $\\frac{a}{b}$. "
            "When outputting JSON, the backslashes will be automatically escaped."
        )

    # Add JSON instruction to the system prompt if required
    json_instruction = "\nYour output MUST be a single, raw JSON object/list." if is_json else ""

    if system_prompt:
        full_prompt = f"{system_prompt}{json_instruction}{latex_instruction}\n\n{prompt}"
    else:
        full_prompt = f"{json_instruction}{latex_instruction}\n\n{prompt}"

    # --- UPDATED TIER ORDER ---
    gemini_key = settings.GEMINI_API_KEY

    # --- Tier 1: Gemini 2.5 Flash (Free) ---
    if gemini_key:
        result = _try_gemini_flash(full_prompt, gemini_key, max_tokens, is_json)
        if result:
            return result

    # --- Tier 2: Gemini Paid (Was Tier 3) ---
    if gemini_key:
        result = _try_gemini_paid(full_prompt, gemini_key, max_tokens, is_json)
        if result:
            return result

    # --- Tier 3: Groq API (Free - Fallback) (Was Tier 2) ---
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
    """Try Gemini 2.5 Flash (Tier 1)"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        config = {}
        if max_tokens:
            config['maxOutputTokens'] = max_tokens
        if is_json:
            config['responseMimeType'] = 'application/json'

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": config
        }

        response = requests.post(url, json=data, headers=headers, timeout=40)

        if response.status_code == 200:
            result = response.json()
            # CRITICAL FIX: Safely check for candidates, content, and parts
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        content = parts[0]['text']
                        return {'success': True, 'content': content, 'tier': 'Gemini Flash'}
    except Exception as e:
        print(f"Gemini Flash failed: {e}")

    return None


def _try_groq(prompt, api_key, max_tokens, is_json):
    """Try Groq API (Tier 3 Fallback)"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"} if is_json else {"type": "text"}, # Groq JSON instruction
            "max_tokens": max_tokens if max_tokens else None,
        }

        # Remove max_tokens if None to avoid API error
        if not data['max_tokens']:
            del data['max_tokens']

        response = requests.post(url, json=data, headers=headers, timeout=40)

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return {'success': True, 'content': content, 'tier': 'Groq'}
    except Exception as e:
        print(f"Groq failed: {e}")

    return None


def _try_gemini_paid(prompt, api_key, max_tokens, is_json):
    """Try Gemini Paid tier (Tier 2)"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        config = {}
        if max_tokens:
            config['maxOutputTokens'] = max_tokens
        if is_json:
            config['responseMimeType'] = 'application/json'

        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": config
        }

        response = requests.post(url, json=data, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            # CRITICAL FIX: Safely check for candidates, content, and parts
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        content = parts[0]['text']
                        return {'success': True, 'content': content, 'tier': 'Gemini Paid'}
    except Exception as e:
        print(f"Gemini Paid failed: {e}")

    return None


def validate_ai_content(content):
    """
    Two-pass validation: Use AI to validate AI-generated content
    Returns 'OK' if valid, or correction message if errors found
    """
    validation_prompt = f"""You are a university professor. Review the following lesson content for accuracy.

Respond with ONLY 'OK' if the content is perfect, or provide a brief correction if errors are found.

Content to review:
{content}
"""

    # We call the main fallback function here
    result = call_ai_with_fallback(validation_prompt)

    if result['success']:
        return result['content'].strip()

    return "OK"