from django.db import transaction
import json

from core.utils.ai_fallback import call_ai_with_fallback
from core.services.curriculum import CurriculumService


def generate_course_modules(course):
    """
    Generate modules for a course.
    Uses curriculum-based generation if curriculum exists,
    otherwise falls back to AI generation.
    """
    from courses.models import Module

    if course.curriculum:
        return generate_curriculum_modules(course)
    
    return generate_ai_modules_for_curriculum(course)


def generate_curriculum_modules(course):
    """Generate modules from curriculum topics"""
    from courses.models import Module
    
    curriculum = course.curriculum
    topics = CurriculumService.get_topics_for_curriculum(curriculum)
    
    if not topics.exists():
        print(f"No topics found for curriculum {curriculum.id}, falling back to AI generation")
        return generate_ai_modules_for_curriculum(course)
    
    with transaction.atomic():
        for index, topic in enumerate(topics):
            Module.objects.create(
                course=course,
                title=topic.title,
                order=index + 1,
                syllabus_topic=topic.description or topic.title,
                lesson_content=None,
                topic=topic
            )
    
    return True


def generate_ai_modules_for_curriculum(course):
    """Generate modules using AI when no curriculum topics exist"""
    from courses.models import Module
    
    if course.school_level and course.term:
        school_level = course.school_level
        term = course.term
        
        prompt = f"""You are creating a study plan for Nigerian secondary school students.

Context:
- Class Level: {school_level.name} ({school_level.level_type})
- Subject: {course.subject}
- Term: {term.name} ({term.instructional_weeks} instructional weeks)

Generate a structured study plan consisting of modules for each week of the term.

Return ONLY a valid JSON object with a single key "modules". 
The "modules" key must contain an array of objects (one per week, up to {term.instructional_weeks} weeks). Each object must have:
- "title": A concise module title (max 100 characters)
- "topic": A specific curriculum topic covered (max 200 characters)
- "week": The week number (1-{term.instructional_weeks})

Do NOT include any text before or after the JSON object. Do NOT use markdown formatting.

Example format:
{{
  "modules": [
    {{"title": "Introduction to the Subject", "topic": "Foundation concepts and overview", "week": 1}},
    {{"title": "Core Concepts", "topic": "Building blocks and fundamental principles", "week": 2}}
  ]
}}"""
        max_tokens = 4000
        num_modules_expected = term.instructional_weeks
    else:
        prompt = f"""You are creating a study plan for Nigerian secondary school students.

Context:
- Subject: {course.subject}

Generate a structured study plan consisting of 12 modules covering the core topics.

Return ONLY a valid JSON object with a single key "modules". 
The "modules" key must contain an array of 12 objects. Each object must have:
- "title": A concise module title (max 100 characters)
- "topic": A specific curriculum topic covered (max 200 characters)

Do NOT include any text before or after the JSON object. Do NOT use markdown formatting.

Example format:
{{
  "modules": [
    {{"title": "Introduction to the Subject", "topic": "Foundation concepts and overview"}},
    {{"title": "Core Concepts", "topic": "Building blocks and fundamental principles"}}
  ]
}}"""
        max_tokens = 4000
        num_modules_expected = 12

    result = call_ai_with_fallback(prompt, max_tokens=max_tokens, is_json=True, subject=course.subject)

    if not result['success']:
        print(f"AI Module Generation Failed for Course {course.id}. Tier: {result.get('tier')}")
        return False

    response_text = result['content']

    try:
        cleaned_text = response_text.strip()

        if cleaned_text.startswith('```'):
            cleaned_text = cleaned_text.split('\n', 1)[1] if '\n' in cleaned_text else cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text.rsplit('```', 1)[0]
            cleaned_text = cleaned_text.strip()

        parsed_data = json.loads(cleaned_text)

        if not isinstance(parsed_data, dict):
            print(f"AI Module Generation Error for Course {course.id}: Response is not a dictionary.")
            return False

        if 'modules' not in parsed_data:
            print(f"AI Module Generation Error for Course {course.id}: Response dictionary does not have a 'modules' key.")
            return False

        module_list = parsed_data['modules']

        if not isinstance(module_list, list) or len(module_list) == 0:
            print(f"AI Module Generation Error for Course {course.id}: Empty module list returned")
            return False

    except json.JSONDecodeError as e:
        print(f"JSON Parsing Failed for Course {course.id}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error parsing modules for Course {course.id}: {e}")
        return False

    with transaction.atomic():
        for index, item in enumerate(module_list):
            Module.objects.create(
                course=course,
                title=item.get('title', 'Untitled Module'),
                order=index + 1,
                syllabus_topic=item.get('topic', 'Unspecified Topic'),
                lesson_content=None,
                topic=None
            )

    return True
