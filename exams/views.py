from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import json
import logging
from .models import Exam, ExamQuestion
from core.utils.ai_fallback import call_ai_with_fallback
from core.services.curriculum import CurriculumService
from courses.models import Course
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus

logger = logging.getLogger(__name__)


@login_required
def start_exam(request, course_id):
    course = get_object_or_404(Course, id=course_id, user=request.user)

    if not request.user.deduct_credits(5):
        messages.error(request, 'Insufficient credits. You need 5 credits to generate a mock exam.')
        return redirect('courses:module_listing', course_id=course.id)

    modules = course.modules.all()
    module_titles = [m.title for m in modules[:15]] 
    topics_text = ", ".join(module_titles) if module_titles else course.subject

    syllabus_content = ""
    context_info = ""
    
    if course.curriculum and course.school_level and course.term:
        school_level = course.school_level
        term = course.term
        context_info = f"{school_level.name} ({school_level.level_type}) - {term.name}"
        
        topics = CurriculumService.get_topics_for_curriculum(course.curriculum)
        if topics.exists():
            topic_titles = [t.title for t in topics[:10]]
            syllabus_content = "Key topics: " + ", ".join(topic_titles)
        else:
            syllabus_content = f"Nigerian {school_level.level_type.lower()} secondary curriculum for {course.subject}"
        
        prompt = f"""You are an expert Nigerian exam creator. Generate EXACTLY 20 multiple-choice questions for {course.subject}.

Class Level: {school_level.name} ({school_level.level_type})
Term: {term.name}
Cover these course topics comprehensively: {topics_text}

STRICT REQUIREMENTS:
1. Return ONLY a valid JSON object with this EXACT structure:
{{
  "questions": [
    {{
      "question": "...",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A"
    }}
  ]
}}

2. Each question MUST have options as an object with keys "A", "B", "C", "D".
3. "answer" MUST be one of: "A", "B", "C", or "D" (uppercase letter).
4. NO markdown formatting, NO code blocks, NO extra text - ONLY the JSON object.
5. Mix difficulty levels (easy, medium, hard).
6. Questions should be appropriate for {school_level.name} students.

{syllabus_content}

Generate 20 comprehensive questions now:"""

    else:
        syllabus_model = {
            'JAMB': JAMBSyllabus,
            'SSCE': SSCESyllabus,
            'JSS': JSSSyllabus
        }.get(course.exam_type)

        if not syllabus_model:
            messages.error(request, f'Syllabus not available for exam type: {course.exam_type}.')
            request.user.add_credits(5)
            return redirect('courses:module_listing', course_id=course.id)

        try:
            syllabus = syllabus_model.objects.get(subject=course.subject)
            syllabus_content = syllabus.syllabus_content[:500]
        except syllabus_model.DoesNotExist:
            messages.error(request, f'Syllabus not found for {course.subject}.')
            request.user.add_credits(5)
            return redirect('courses:module_listing', course_id=course.id)

        context_info = f"{course.exam_type} {course.subject}"
        
        prompt = f"""You are an expert Nigerian exam creator. Generate EXACTLY 20 multiple-choice questions for {course.exam_type} {course.subject}.

Cover these course topics comprehensively: {topics_text}

STRICT REQUIREMENTS:
1. Return ONLY a valid JSON object with this EXACT structure:
{{
  "questions": [
    {{
      "question": "...",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A"
    }}
  ]
}}

2. Each question MUST have options as an object with keys "A", "B", "C", "D".
3. "answer" MUST be one of: "A", "B", "C", or "D" (uppercase letter).
4. NO markdown formatting, NO code blocks, NO extra text - ONLY the JSON object.
5. Mix difficulty levels (easy, medium, hard).

Syllabus reference:
{syllabus_content}

Generate 20 comprehensive questions now:"""

    exam = Exam.objects.create(
        user=request.user,
        course=course,
        title=f"{context_info or course.display_name} - Mock Exam"
    )

    try:
        result = call_ai_with_fallback(prompt, max_tokens=4000, is_json=True, subject=course.subject)

        if not result['success']:
            logger.error(f"AI failure (success=False): {result.get('content')}")
            raise Exception("AI service unavailable")

        response_text = result['content'].strip()

        if response_text.startswith('```'):
            lines = response_text.split('\n')
            if len(lines) > 1:
                response_text = '\n'.join(lines[1:])
            else:
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text.rsplit('```', 1)[0]
            response_text = response_text.strip()

        parsed_data = json.loads(response_text)

        if isinstance(parsed_data, list):
            questions_data = parsed_data
        elif isinstance(parsed_data, dict) and 'questions' in parsed_data:
            questions_data = parsed_data['questions']
        else:
            raise ValueError("Invalid response format: 'questions' key not found")

        created_count = 0
        for q_data in questions_data[:20]:
            if not isinstance(q_data, dict):
                continue
            if 'question' not in q_data or 'options' not in q_data or 'answer' not in q_data:
                continue
            
            ExamQuestion.objects.create(
                exam=exam,
                question_text=q_data['question'],
                options=q_data['options'],
                correct_answer=q_data['answer']
            )
            created_count += 1

        if created_count == 0:
            raise ValueError("No valid questions were generated by the AI")

        exam.total_questions = created_count
        exam.save()

    except Exception as e:
        logger.error(f"Exam generation error: {e}")
        exam.delete()
        request.user.add_credits(5)
        messages.error(request, 'Sorry, the AI failed to generate a valid exam. Your credits have been refunded. Please try again.')
        return redirect('courses:module_listing', course_id=course.id)

    return redirect("exams:take_exam", exam_id=exam.id)


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, user=request.user)

    if exam.completed_at:
        messages.info(request, "This exam has already been completed.")
        return redirect("exams:results", exam_id=exam.id)

    questions = exam.exam_questions.all()

    if request.method == "POST":
        score = 0
        for q in questions:
            user_ans = request.POST.get(f'question_{q.id}')
            q.user_answer = user_ans
            q.is_correct = user_ans == q.correct_answer
            if q.is_correct:
                score += 1
            q.save()

        exam.score = score
        exam.completed_at = timezone.now()
        exam.save()

        return redirect("exams:results", exam_id=exam.id)

    return render(request, "exams/take_exam.html", {"exam": exam, "questions": questions})


@login_required
def results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, user=request.user)
    return render(request, "exams/results.html", {"exam": exam})
