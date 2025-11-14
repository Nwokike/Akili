from django.db import transaction
import json

from core.utils.ai_fallback import call_ai_with_fallback


def generate_course_modules(course):
    """
    Generates 15 Modules for a given Course using AI and syllabus data.
    Returns True on success, False on failure.
    """
    from courses.models import Module
    from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus
    
    # 1. Get syllabus content
    syllabus_content = ""
    try:
        if course.exam_type == 'JAMB':
            syllabus = JAMBSyllabus.objects.get(subject=course.subject)
            syllabus_content = syllabus.syllabus_content
        elif course.exam_type == 'SSCE':
            syllabus = SSCESyllabus.objects.get(subject=course.subject)
            syllabus_content = syllabus.syllabus_content
        elif course.exam_type == 'JSS':
            syllabus = JSSSyllabus.objects.get(subject=course.subject)
            syllabus_content = syllabus.syllabus_content
    except Exception as e:
        print(f"Syllabus not found for {course.exam_type} {course.subject}: {e}")
        syllabus_content = ""
    
    # 2. AI Prompt Construction
    prompt = f"""
    Based on the following official {course.exam_type} syllabus for {course.subject}, 
    generate a structured study plan consisting of EXACTLY 15 modules.
    
    Syllabus Content:
    {syllabus_content if syllabus_content else "General curriculum topics"}
    
    The output MUST be a single JSON list of 15 objects. Each object must have 
    two keys: "title" (a concise module title) and "topic" (a specific 
    syllabus topic covered by the module).
    
    JSON Output Format:
    [
        {{"title": "Introduction to Linear Motion", "topic": "Uniform acceleration and deceleration"}},
        {{"title": "Forces and Newton's Laws", "topic": "Newton's three laws of motion"}}
    ]
    """
    
    # 3. Call AI with fallback system
    result = call_ai_with_fallback(prompt, max_tokens=2000, is_json=True)
    
    if not result['success']:
        print(f"AI Module Generation Failed for Course {course.id}. Tier: {result.get('tier')}")
        return False
    
    response_text = result['content']
    
    # 4. Parse JSON response
    try:
        if response_text.startswith('```json'):
            response_text = response_text.strip().lstrip('```json').rstrip('```')
        elif response_text.startswith('```'):
            response_text = response_text.strip().lstrip('```').rstrip('```')
            
        module_list = json.loads(response_text)
        
        if not isinstance(module_list, list) or len(module_list) == 0:
            raise ValueError("AI response was not a valid list.")
        
        # Validate exactly 15 modules as per spec
        if len(module_list) != 15:
            print(f"AI returned {len(module_list)} modules instead of 15 for Course {course.id}")
            return False
             
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON Parsing Failed for Course {course.id}: {e}")
        return False
    
    # 5. Save modules to database
    from courses.models import Module
    with transaction.atomic():
        for index, item in enumerate(module_list):
            Module.objects.create(
                course=course,
                title=item.get('title', 'Untitled Module'),
                order=index + 1,
                syllabus_topic=item.get('topic', 'Unspecified Topic'),
                lesson_content=None  # Lesson content will be generated on-demand
            )
        
    return True