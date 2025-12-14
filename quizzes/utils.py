from django.db import transaction
import json
from core.utils.ai_fallback import call_ai_with_fallback 
from users.models import CustomUser 
from courses.models import Module, Course
from .models import QuizAttempt


def generate_quiz_and_save(module: Module, user: CustomUser, num_questions=5) -> tuple[bool, str]:
    course = module.course
    course_subject = course.subject
    
    if course.school_level and course.term:
        context_info = f"{course.school_level.name} ({course.school_level.level_type})"
        curriculum_ref = f"Nigerian {course.school_level.level_type.lower()} secondary curriculum"
    else:
        context_info = f"{course.exam_type} curriculum"
        curriculum_ref = f"{course.exam_type} curriculum"

    prompt = f"""You are an expert Nigerian education assessor. Generate a quiz of EXACTLY {num_questions} multiple-choice questions for "{course_subject}" ({context_info}), topic: "{module.title}".

CRITICAL REQUIREMENTS - FOLLOW EXACTLY:

1. Return ONLY a valid JSON object with this EXACT structure:
{{
  "questions": [
    {{
      "question_text": "...",
      "choices": ["...", "...", "...", "..."],
      "correct_index": 0,
      "explanation": "..."
    }}
  ]
}}

2. Each question MUST have EXACTLY 4 choices in the "choices" array.

3. "correct_index" MUST be an integer 0-3 (NOT a letter like "A" or "B").

4. NO markdown code blocks (```json), NO extra text before or after the JSON object.

5. Test your JSON is valid before responding.

6. Questions should be appropriate for {context_info} students following the {curriculum_ref}.

Example:
{{
  "questions": [
    {{"question_text": "What is the capital of Nigeria?", "choices": ["Lagos", "Abuja", "Kano", "Port Harcourt"], "correct_index": 1, "explanation": "Abuja has been the capital of Nigeria since 1991."}}
  ]
}}

Generate {num_questions} questions now with perfect JSON:"""

    result = call_ai_with_fallback(prompt, max_tokens=3000, is_json=True, subject=course_subject) 

    if not result['success']:
        print(f"AI Quiz Generation FAILED. Tier: {result.get('tier')}. Error: {result.get('content')[:100]}...")
        return False, "AI service is unavailable or returned an unrecoverable error."

    response_text = result['content']

    print(f"\n--- RAW AI RESPONSE START (Tier: {result.get('tier')}) ---\n{response_text[:500]}...\n--- RAW AI RESPONSE END ---\n")

    try:
        cleaned_text = response_text.strip()

        if cleaned_text.startswith('```'):
            lines = cleaned_text.split('\n')
            if len(lines) > 1:
                cleaned_text = '\n'.join(lines[1:])
            else:
                cleaned_text = cleaned_text[3:]
            
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text.rsplit('```', 1)[0]
            
            cleaned_text = cleaned_text.strip()

        parsed_data = json.loads(cleaned_text)

        if not isinstance(parsed_data, dict):
            if isinstance(parsed_data, list):
                parsed_data = {"questions": parsed_data}
            else:
                raise ValueError(f"AI response is not a dictionary or list. Got: {type(parsed_data)}")

        if 'questions' not in parsed_data:
            raise ValueError("AI response missing 'questions' key.")

        question_list = parsed_data['questions']

        if not isinstance(question_list, list) or len(question_list) == 0:
            raise ValueError("AI response 'questions' is empty or not a list.")

        for i, q in enumerate(question_list):
            if not isinstance(q, dict):
                raise ValueError(f"Question {i} is not a dictionary.")
            if 'question_text' not in q or 'choices' not in q or 'correct_index' not in q:
                raise ValueError(f"Question {i} missing required fields.")

    except json.JSONDecodeError as e:
        print(f"JSON Parsing FAILED for Quiz generation: {e}")
        print(f"Raw response (first 500 chars): {response_text[:500]}")
        return False, "AI generated invalid JSON. Please try again."
    except ValueError as e:
        print(f"JSON Validation FAILED: {e}")
        print(f"Raw response (first 500 chars): {response_text[:500]}")
        return False, "AI response format is invalid. Please try again."

    with transaction.atomic():

        quiz_attempt = QuizAttempt.objects.create(
            user=user,
            module=module,
            score=0,
            questions_data=question_list,
            total_questions=len(question_list)
        )

    return True, str(quiz_attempt.id)
