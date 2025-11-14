# quizzes/utils.py

from django.db import transaction
import json
# Import utilities and models
from core.utils.ai_fallback import call_ai_with_fallback 
from users.models import CustomUser 
from courses.models import Module, Course # Import Course to ensure correct structure
from .models import QuizAttempt


def generate_quiz_and_save(module: Module, user: CustomUser, num_questions=5) -> tuple[bool, str]:
    """
    Calls the AI to generate a structured quiz based on a module, saves the structure 
    to a new QuizAttempt record, and returns the result and the new quiz ID.
    
    Returns (success: bool, quiz_id/error_message: str).
    """
    
    # CRITICAL FIX: Access subject and exam_type via the module's linked course
    course_subject = module.course.subject
    course_exam_type = module.course.exam_type
    
    # 1. Construct the Prompt
    prompt = f"""
    You are an expert Nigerian education assessor. Generate a quiz consisting 
    of EXACTLY {num_questions} multiple-choice questions (MCQs) for the subject 
    "{course_subject}", focusing on the topic: "{module.title}" (from the {course_exam_type} curriculum).
    
    Each question MUST have 4 choices. The output MUST be a single JSON list of 
    {num_questions} objects.
    
    JSON Output Format Requirements:
    - Use only the keys: "question_text", "choices" (list of 4 strings), "correct_index" (integer 0-3), and "explanation".
    - Format all mathematical or scientific content using LaTeX (e.g., $E=mc^2$).
    
    Example Structure:
    [
        {{"question_text": "Calculate the velocity of a car accelerating at $2 \\, m/s^2$ for $5 \\, s$.",
        "choices": ["10 m/s", "2.5 m/s", "15 m/s", "20 m/s"],
        "correct_index": 0,
        "explanation": "Velocity = acceleration x time (2 * 5 = 10 m/s)."}},
        // ... ({num_questions - 1} more question objects)
    ]
    """
    
    # 2. Call the AI with Fallback
    result = call_ai_with_fallback(prompt, max_tokens=3000, is_json=True) 
    
    if not result['success']:
        print(f"AI Quiz Generation FAILED. Tier: {result.get('tier')}. Error: {result.get('content')[:100]}...")
        return False, "AI service is unavailable or returned an unrecoverable error."
    
    response_text = result['content']
    
    # DEBUG LINE: Print the raw AI response to terminal
    print(f"\n--- RAW AI RESPONSE START (Tier: {result.get('tier')}) ---\n{response_text[:500]}...\n--- RAW AI RESPONSE END ---\n")
    
    # 3. Robust JSON Parsing
    try:
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') 
        
        if json_start == -1 or json_end == -1:
             raise ValueError("Could not find valid JSON list boundaries in AI response.")

        clean_json_text = response_text[json_start:json_end + 1]
        question_list = json.loads(clean_json_text)
        
        if not isinstance(question_list, list) or len(question_list) == 0:
             raise ValueError("AI response was empty or malformed.")
             
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON Parsing FAILED for Quiz generation: Error: {e}")
        return False, "Failed to decode AI response into questions."
    
    # 4. Save the Quiz Attempt Record
    with transaction.atomic():
        
        quiz_attempt = QuizAttempt.objects.create(
            user=user,
            module=module,
            score=0,
            questions_data=question_list,
            total_questions=len(question_list)
        )
        
    return True, str(quiz_attempt.id)