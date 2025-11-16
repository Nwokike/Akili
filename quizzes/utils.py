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

    # 1. Construct the Prompt with STRICT JSON requirements
    prompt = f"""You are an expert Nigerian education assessor. Generate a quiz of EXACTLY {num_questions} multiple-choice questions for "{course_subject}" ({course_exam_type} curriculum), topic: "{module.title}".

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

4. CRITICAL LATEX FORMATTING - Use DOUBLE-ESCAPED backslashes in ALL math expressions:
   - Write "\\\\frac{{a}}{{b}}" NOT "\\frac{{a}}{{b}}"
   - Write "$a \\\\times b$" NOT "$a \\times b$"
   - Write "$$\\\\int_a^b f(x)dx$$" NOT "$$\\int_a^b f(x)dx$$"
   - Write "\\\\sqrt{{x}}" NOT "\\sqrt{{x}}"
   - Write "\\\\sum_{{i=1}}^{{n}}" NOT "\\sum_{{i=1}}^{{n}}"
   - This applies to question_text, choices, AND explanation

5. NO markdown code blocks (```json), NO extra text before or after the JSON object.

6. Test your JSON is valid before responding.

Example:
{{
  "questions": [
    {{"question_text": "Calculate $5 \\\\times 3$", "choices": ["$15$", "$8$", "$10$", "$20$"], "correct_index": 0, "explanation": "Multiplication: $5 \\\\times 3 = 15$"}}
  ]
}}

Generate {num_questions} questions now with perfect JSON and double-escaped LaTeX:"""

    # 2. Call the AI with Fallback
    result = call_ai_with_fallback(prompt, max_tokens=3000, is_json=True) 

    if not result['success']:
        print(f"AI Quiz Generation FAILED. Tier: {result.get('tier')}. Error: {result.get('content')[:100]}...")
        return False, "AI service is unavailable or returned an unrecoverable error."

    response_text = result['content']

    # DEBUG LINE: Print the raw AI response to terminal
    print(f"\n--- RAW AI RESPONSE START (Tier: {result.get('tier')}) ---\n{response_text[:500]}...\n--- RAW AI RESPONSE END ---\n")

    # 3. ROBUST JSON Parsing with extensive error handling
    try:
        # Clean the response text thoroughly
        cleaned_text = response_text.strip()

        # Remove markdown code blocks if present (```json or ```)
        if cleaned_text.startswith('```'):
            lines = cleaned_text.split('\n')
            # Remove first line (```json or ```)
            if len(lines) > 1:
                cleaned_text = '\n'.join(lines[1:])
            else:
                cleaned_text = cleaned_text[3:]
            
            # Remove closing ```
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text.rsplit('```', 1)[0]
            
            cleaned_text = cleaned_text.strip()

        # Try to parse JSON
        parsed_data = json.loads(cleaned_text)

        # Validate structure: must be a dictionary
        if not isinstance(parsed_data, dict):
            # If it's a list, wrap it in {"questions": [...]}
            if isinstance(parsed_data, list):
                parsed_data = {"questions": parsed_data}
            else:
                raise ValueError(f"AI response is not a dictionary or list. Got: {type(parsed_data)}")

        # Extract questions list
        if 'questions' not in parsed_data:
            raise ValueError("AI response missing 'questions' key.")

        question_list = parsed_data['questions']

        # Validate questions list
        if not isinstance(question_list, list) or len(question_list) == 0:
            raise ValueError("AI response 'questions' is empty or not a list.")

        # Validate each question has required fields
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