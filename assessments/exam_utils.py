"""
Utilities for generating course-wide mock exams using AI.
"""
import logging
import json
import re
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_exam_questions(course, num_questions=20):
    """
    Generate comprehensive exam questions covering all modules in a course.
    
    Args:
        course: Course instance
        num_questions: Number of questions to generate (default 20)
    
    Returns:
        List of question dictionaries with question, options, correct_index, explanation
    """
    from core.utils.ai_service import get_ai_client
    
    modules = course.modules.all().order_by('order')
    if not modules.exists():
        return []
    
    topics = [f"Module {m.order}: {m.syllabus_topic}" for m in modules[:14]]
    topics_str = "\n".join(topics)
    
    level_name = course.school_level.name if course.school_level else "Secondary School"
    term_name = course.term.name if course.term else "First Term"
    
    prompt = f"""Generate a comprehensive mock examination for Nigerian secondary school students.

Subject: {course.subject}
Level: {level_name}
Term: {term_name}

Topics to cover (spread questions across all topics):
{topics_str}

Generate exactly {num_questions} multiple choice questions. Each question should:
1. Test understanding, not just memorization
2. Be appropriate for {level_name} students
3. Cover different topics evenly
4. Follow Nigerian curriculum standards

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Clear question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Brief explanation of why this answer is correct",
    "topic": "Module number this relates to"
  }}
]

Important: Return ONLY the JSON array, no additional text."""

    try:
        client = get_ai_client()
        if not client:
            logger.error("No AI client available for exam generation")
            return []
        
        response = client.generate_content(prompt)
        response_text = response.text.strip()
        
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group()
        
        questions = json.loads(response_text)
        
        valid_questions = []
        for q in questions:
            if (isinstance(q, dict) and 
                'question' in q and 
                'options' in q and 
                'correct_index' in q and
                isinstance(q['options'], list) and
                len(q['options']) >= 4):
                
                valid_questions.append({
                    'question': q['question'],
                    'options': q['options'][:4],
                    'correct_index': int(q.get('correct_index', 0)) % 4,
                    'explanation': q.get('explanation', ''),
                    'topic': q.get('topic', '')
                })
        
        return valid_questions[:num_questions]
        
    except Exception as e:
        logger.error(f"Error generating exam questions: {e}")
        return []


def generate_exam_and_save(course, user, num_questions=20):
    """
    Generate a mock exam and save it to the database.
    
    Args:
        course: Course instance
        user: User taking the exam
        num_questions: Number of questions (default 20)
    
    Returns:
        Tuple of (success, exam_id_or_error)
    """
    from assessments.models import CourseExam
    
    try:
        questions = generate_exam_questions(course, num_questions)
        
        if not questions or len(questions) < 5:
            return False, "Failed to generate sufficient exam questions"
        
        exam = CourseExam.objects.create(
            user=user,
            course=course,
            total_questions=len(questions),
            questions_data=questions
        )
        
        return True, exam.id
        
    except Exception as e:
        logger.error(f"Error creating exam: {e}")
        return False, str(e)
