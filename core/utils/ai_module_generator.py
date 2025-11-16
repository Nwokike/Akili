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
    prompt = f"""Based on the following official {course.exam_type} syllabus for {course.subject}, generate a structured study plan consisting of EXACTLY 15 modules.

Syllabus Content:
{syllabus_content if syllabus_content else "General curriculum topics for " + course.subject}

Return ONLY a valid JSON array with EXACTLY 15 objects. Each object must have:
- "title": A concise module title (max 100 characters)
- "topic": A specific syllabus topic covered (max 200 characters)

Do NOT include any text before or after the JSON array. Do NOT use markdown formatting.

Example format:
[
  {{"title": "Introduction to Linear Motion", "topic": "Uniform acceleration and deceleration"}},
  {{"title": "Forces and Newton's Laws", "topic": "Newton's three laws of motion"}}
]"""
    
    # 3. Call AI with fallback system
    result = call_ai_with_fallback(prompt, max_tokens=2000, is_json=True)
    
    if not result['success']:
        print(f"AI Module Generation Failed for Course {course.id}. Tier: {result.get('tier')}")
        return False
    
    response_text = result['content']
    
    # 4. Parse JSON response with robust cleaning
    try:
        # Clean the response text thoroughly
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_text.startswith('```'):
            # Remove ```json or ``` at the start
            cleaned_text = cleaned_text.split('\n', 1)[1] if '\n' in cleaned_text else cleaned_text[3:]
            # Remove ``` at the end
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text.rsplit('```', 1)[0]
            cleaned_text = cleaned_text.strip()
        
        # Try to parse JSON
        module_list = json.loads(cleaned_text)
        
        # Validate it's a list
        if not isinstance(module_list, list):
            print(f"AI Module Generation Error for Course {course.id}: Response is not a list. Got: {type(module_list)}")
            print(f"Response preview: {str(module_list)[:200]}")
            return False
        
        # Validate we have modules
        if len(module_list) == 0:
            print(f"AI Module Generation Error for Course {course.id}: Empty module list returned")
            return False
        
        # Accept 10-15 modules (be flexible)
        if len(module_list) < 10:
            print(f"AI Module Generation Error for Course {course.id}: Only {len(module_list)} modules returned, need at least 10")
            return False
        
        # If we got more than 15, trim to 15
        if len(module_list) > 15:
            print(f"AI returned {len(module_list)} modules, trimming to 15 for Course {course.id}")
            module_list = module_list[:15]
        
        # If we got 10-14, pad to 15 with review modules
        while len(module_list) < 15:
            module_list.append({
                "title": f"Review and Practice {len(module_list) + 1}",
                "topic": f"Comprehensive review of {course.subject} concepts"
            })
             
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Failed for Course {course.id}: {e}")
        print(f"Response text was: {response_text[:500]}")
        return False
    except Exception as e:
        print(f"Unexpected error parsing modules for Course {course.id}: {e}")
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