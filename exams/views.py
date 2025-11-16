from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Exam, ExamQuestion
from core.utils.ai_fallback import call_ai_with_fallback
import json


@login_required
def start_exam(request, module_id):
    """
    Generate a temporary mock exam using AI for a specific module.
    Cost: 5 credits
    Exams are temporary - old completed exams are deleted when creating new ones.
    """
    from courses.models import Module
    from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus
    
    module = get_object_or_404(Module, id=module_id, course__user=request.user)
    
    # CRITICAL FIX: Delete all completed exams for this user and module (temporary exams)
    Exam.objects.filter(
        user=request.user,
        module=module,
        completed_at__isnull=False
    ).delete()
    
    # Deduct 5 credits
    if not request.user.deduct_credits(5):
        messages.error(request, 'Insufficient credits. You need 5 credits to generate a mock exam.')
        return redirect('courses:module_listing', course_id=module.course.id)
    
    # Get syllabus based on exam type
    syllabus_model = {
        'JAMB': JAMBSyllabus,
        'SSCE': SSCESyllabus,
        'JSS': JSSSyllabus
    }.get(module.course.exam_type)
    
    try:
        syllabus = syllabus_model.objects.get(subject=module.course.subject)
    except:
        messages.error(request, 'Syllabus not available for this subject.')
        # Refund credits since we failed before generating
        request.user.add_credits(5)
        return redirect('courses:module_listing', course_id=module.course.id)

    # Create exam
    exam = Exam.objects.create(
        user=request.user,
        module=module,
        title=f"{module.course.exam_type} {module.course.subject} Mock Exam"
    )

    # Generate questions using AI with STRICT JSON requirements
    prompt = f"""You are an expert Nigerian exam creator. Generate EXACTLY 20 multiple-choice questions for {module.course.exam_type} {module.course.subject} based on this topic: "{module.title}".

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

5. NO markdown formatting, NO code blocks, NO extra text - ONLY the JSON object.

Syllabus reference:
{syllabus.syllabus_content[:500]}

Generate 20 questions now:"""

    try:
        result = call_ai_with_fallback(prompt, max_tokens=4000, is_json=True)
        
        if not result['success']:
            messages.error(request, 'Sorry, the AI tutor is busy. Please try again.')
            exam.delete()
            request.user.add_credits(5)  # Refund credits
            return redirect('courses:module_listing', course_id=module.course.id)
        
        # ROBUST JSON Parsing
        response_text = result['content'].strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            if len(lines) > 1:
                response_text = '\n'.join(lines[1:])
            else:
                response_text = response_text[3:]
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
            raise ValueError("Invalid response format")
        
        # Create exam questions
        created_count = 0
        for q_data in questions_data[:20]:
            if isinstance(q_data, dict) and 'question' in q_data and 'options' in q_data and 'answer' in q_data:
                ExamQuestion.objects.create(
                    exam=exam,
                    question_text=q_data['question'],
                    options=q_data['options'],
                    correct_answer=q_data['answer']
                )
                created_count += 1
        
        if created_count == 0:
            raise ValueError("No valid questions generated")
        
        exam.total_questions = created_count
        exam.save()
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Exam generation error: {e}")
        messages.error(request, 'Sorry, the AI tutor is busy. Please try again.')
        exam.delete()
        request.user.add_credits(5)  # Refund credits
        return redirect('courses:module_listing', course_id=module.course.id)
    except Exception as e:
        print(f"Unexpected exam error: {e}")
        messages.error(request, 'Sorry, the AI tutor is busy. Please try again.')
        exam.delete()
        request.user.add_credits(5)  # Refund credits
        return redirect('courses:module_listing', course_id=module.course.id)

    return redirect("exams:take_exam", exam_id=exam.id)


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, user=request.user)
    questions = exam.exam_questions.all()

    if request.method == "POST":
        score = 0
        for q in questions:
            user_ans = request.POST.get(str(q.id))
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
