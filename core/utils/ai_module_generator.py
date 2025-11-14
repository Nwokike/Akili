from django.db import transaction
from courses.models import Course, Module # FIX: Removed CachedLesson import
import json
import uuid 

# Import the corrected fallback utility
from core.utils.ai_fallback import call_ai_with_fallback 

def trigger_module_generation(course: Course):
    """
    Generates modules and saves them to the Module model, skipping the 
    non-existent CachedLesson model creation.
    """
    
    # ... (AI Prompt Construction remains the same) ...
    prompt = f"""
    You are an expert Nigerian education curriculum planner. Generate a structured 
    study plan consisting of EXACTLY 15 modules for a student preparing for the 
    {course.exam_type} exam in the subject: {course.subject}.
    
    The output MUST be a single JSON list of 15 objects. Each object must have 
    two keys: "title" (a concise module title) and "topic" (a single specific 
    syllabus topic covered by the module).
    
    JSON Output Format Example:
    [
        {{"title": "Introduction to Linear Motion", "topic": "Uniform acceleration and deceleration"}},
        ... (13 more modules)
    ]
    """
    
    # ... (AI Call and JSON Parsing remain the same) ...
    result = call_ai_with_fallback(prompt, max_tokens=1500, is_json=True) 
    
    if not result['success']:
        print(f"AI Module Generation Failed for Course {course.id}. Tier: {result.get('tier')}")
        return False
    
    response_text = result['content']
    
    try:
        json_start = response_text.find('[')
        json_end = response_text.rfind(']') 
        
        if json_start == -1 or json_end == -1:
             raise ValueError("Could not find valid JSON list boundaries.")

        clean_json_text = response_text[json_start:json_end + 1]
        module_list = json.loads(clean_json_text)
        
        if not isinstance(module_list, list) or len(module_list) == 0:
             raise ValueError("AI response was not a valid JSON list object.")
             
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON Parsing Failed for Course {course.id}: Error: {e}")
        return False
    
    # --- Data Saving (FIXED) ---
    with transaction.atomic():
        for index, item in enumerate(module_list):
            
            # REMOVED: Creation of CachedLesson and 'lesson_to_use' variable.
            # We assume lesson content will be stored/generated later based on the module title.
            
            # Create the Module linking to the Course
            Module.objects.create(
                course=course,
                title=item.get('title', 'Untitled Module'),
                order=index + 1,
                syllabus_topic=item.get('topic', 'Unspecified Topic'),
                # REMOVED: lesson_content=lesson_to_use
            )
            
        # 4. Deduct Credits (If applicable, ensure this is done)
        # course.user.deduct_credits(amount=5)
        
    return True