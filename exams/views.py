from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Exam, ExamQuestion
from core.utils.ai_fallback import call_ai_with_fallback
import json

# Import the models we need for this view
from courses.models import Course
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus


@login_required
def start_exam(request, course_id):
    """
    Generate a course-wide mock exam using AI covering all course modules.
    Cost: 5 credits
    Exams are temporary - old completed exams are deleted when creating new ones.
    """

    # We get the course object once at the top
    course = get_object_or_404(Course, id=course_id, user=request.user)

    # Delete all completed exams for this user and course (temporary exams)
    Exam.objects.filter(
        user=request.user,
        course=course,
        completed_at__isnull=False
    ).delete()

    # Deduct 5 credits
    if not request.user.deduct_credits(5):
        messages.error(request, 'Insufficient credits. You need 5 credits to generate a mock exam.')
        # FIX 1 (Architect Finding 1 & 2): Redirect uses the 'course.id'
        return redirect('courses:module_listing', course_id=course.id)

    # Get syllabus based on exam type
    syllabus_model = {
        'JAMB': JAMBSyllabus,
        'SSCE': SSCESyllabus,
        'JSS': JSSSyllabus
    }.get(course.exam_type)

    # --- FIX 2 (Architect Finding 3) ---
    # Add a safety check in case the exam_type is not in our dict
    if not syllabus_model:
        messages.error(request, f'Syllabus not available for exam type: {course.exam_type}.')
        request.user.add_credits(5) # Refund credits
        return redirect('courses:module_listing', course_id=course.id)

    try:
        syllabus = syllabus_model.objects.get(subject=course.subject)
    except syllabus_model.DoesNotExist:
        messages.error(request, f'Syllabus not found for {course.subject}.')
        request.user.add_credits(5) # Refund credits
        # FIX 1 (Architect Finding 1 & 2): Redirect uses the 'course.id'
        return redirect('courses:module_listing', course_id=course.id)

    # Create exam
    exam = Exam.objects.create(
        user=request.user,
        course=course,
        title=f"{course.exam_type} {course.subject} - Course-Wide Mock Exam"
    )

    # Get all modules for comprehensive topic coverage
    modules = course.modules.all()
    # Get up to 15 module titles to guide the AI
    module_titles = [m.title for m in modules[:15]] 
    topics_text = ", ".join(module_titles) if module_titles else course.subject

    # --- FIX 3: Stricter prompt for Gemini to fix JSON and LaTeX errors ---
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
4. CRITICAL: For ALL LaTeX math, use DOUBLE-ESCAPED backslashes.
   - Write "\\\\frac{{a}}{{b}}" NOT "\\frac{{a}}{{b}}"
   - Write "$a \\\\times b$" NOT "$a \\times b$"
   - Write "\\\\sqrt{{x}}" NOT "\\sqrt{{x}}"

5. NO markdown formatting, NO code blocks, NO extra text - ONLY the JSON object.
6. Mix difficulty levels (easy, medium, hard).

Syllabus reference:
{syllabus.syllabus_content[:500]}

Generate 20 comprehensive questions now:"""

    try:
        result = call_ai_with_fallback(prompt, max_tokens=4000, is_json=True)

        if not result['success']:
            # --- FIX 4 (Architect Finding 1 & 2) & Friendly Error ---
            print(f"AI failure (success=False): {result.get('content')}")
            messages.error(request, 'Sorry, the AI tutor is busy. Please try again.')
            exam.delete()
            request.user.add_credits(5)  # Refund credits
            return redirect('courses:module_listing', course_id=course.id)

        # --- FIX 5: ROBUST JSON Parsing ---
        response_text = result['content'].strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            if len(lines) > 1:
                response_text = '\n'.join(lines[1:]) # Get content after ```json
            else:
                response_text = response_text[3:] # Remove ```
            if response_text.endswith('```'):
                response_text = response_text.rsplit('```', 1)[0]
            response_text = response_text.strip()

        # Parse JSON
        parsed_data = json.loads(response_text)

        # Handle both {"questions": [...]} and direct array [...]
        if isinstance(parsed_data, list):
            questions_data = parsed_data
        elif isinstance(parsed_data, dict) and 'questions' in parsed_data:
            questions_data = parsed_data['questions']
        else:
            raise ValueError("Invalid response format: 'questions' key not found or not a list")

        # Create exam questions
        created_count = 0
        for q_data in questions_data[:20]:
            # Basic validation to ensure the data is usable
            if isinstance(q_data, dict) and 'question' in q_data and 'options' in q_data and 'answer' in q_data:
                ExamQuestion.objects.create(
                    exam=exam,
                    question_text=q_data['question'],
                    options=q_data['options'],
                    correct_answer=q_data['answer']
                )
                created_count += 1

        if created_count == 0:
            raise ValueError("No valid questions were generated by the AI.")

        exam.total_questions = created_count
        exam.save()

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # --- FIX 4 (Architect Finding 1 & 2) & Friendly Error ---
        print(f"Exam generation JSON/parsing error: {e}")
        messages.error(request, 'Sorry, the AI failed to generate a valid exam. Please try again.')
        exam.delete()
        request.user.add_credits(5)  # Refund credits
        return redirect('courses:module_listing', course_id=course.id)
    except Exception as e:
        # --- FIX 4 (Architect Finding 1 & 2) & Friendly Error ---
        print(f"Unexpected exam error: {e}")
        messages.error(request, 'An unexpected error occurred. Please try again.')
        exam.delete()
        request.user.add_credits(5)  # Refund credits
        return redirect('courses:module_listing', course_id=course.id)

    # Success! Redirect to the exam-taking page
    return redirect("exams:take_exam", exam_id=exam.id)


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, user=request.user)

    # Prevent user from taking an already completed exam
    if exam.completed_at:
        messages.info(request, "This exam has already been completed.")
        return redirect("exams:results", exam_id=exam.id)

    questions = exam.exam_questions.all()

    if request.method == "POST":
        score = 0
        for q in questions:
            user_ans = request.POST.get(f'question_{q.id}') # Match form name
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