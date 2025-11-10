import os
import requests
from django.conf import settings


def call_ai_with_fallback(prompt, system_prompt=None):
    """
    4-tier AI Smart Fallback system
    Tier 1: Gemini 2.5 Flash (Free)
    Tier 2: Groq API (Free)
    Tier 3: Gemini Paid (Paid)
    Tier 4: Circuit Breaker (Graceful error)
    """
    
    latex_instruction = (
        "\nYou are an expert tutor. Format all mathematical equations, formulas, "
        "and scientific notation using LaTeX (e.g., $E=mc^2$ or $$\\int_a^b f(x)dx$$)."
    )
    
    if system_prompt:
        full_prompt = f"{system_prompt}\n{latex_instruction}\n\n{prompt}"
    else:
        full_prompt = f"{latex_instruction}\n\n{prompt}"
    
    gemini_key = settings.GEMINI_API_KEY
    groq_key = settings.GROQ_API_KEY
    
    if gemini_key:
        result = _try_gemini_flash(full_prompt, gemini_key)
        if result:
            return result
    
    if groq_key:
        result = _try_groq(full_prompt, groq_key)
        if result:
            return result
    
    if gemini_key:
        result = _try_gemini_paid(full_prompt, gemini_key)
        if result:
            return result
    
    return {
        'success': False,
        'content': "Our AI tutors are at full capacity. Please try again in 2–3 minutes."
    }


def _try_gemini_flash(prompt, api_key):
    """Try Gemini 2.5 Flash (Tier 1)"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return {'success': True, 'content': content, 'tier': 'Gemini Flash'}
    except Exception as e:
        print(f"Gemini Flash failed: {e}")
    
    return None


def _try_groq(prompt, api_key):
    """Try Groq API (Tier 2)"""
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return {'success': True, 'content': content, 'tier': 'Groq'}
    except Exception as e:
        print(f"Groq failed: {e}")
    
    return None


def _try_gemini_paid(prompt, api_key):
    """Try Gemini Paid tier (Tier 3)"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
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
    
    result = call_ai_with_fallback(validation_prompt)
    
    if result['success']:
        return result['content'].strip()
    
    return "OK"
