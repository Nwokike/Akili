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
    Generate a mock exam using AI for a specific module.
    Cost: 5 credits
    """
    from courses.models import Module
    from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus
    
    module = get_object_or_404(Module, id=module_id, course__user=request.user)
    
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
        return redirect('courses:module_listing', course_id=module.course.id)

    # Create exam
    exam = Exam.objects.create(
        user=request.user,
        module=module,
        title=f"{module.course.exam_type} {module.course.subject} Mock Exam"
    )

    # Generate questions using AI
    prompt = f"""Based on this syllabus:\n\n{syllabus.syllabus_content}\n\n
Generate 20 multiple-choice questions for {module.course.exam_type} {module.course.subject}.
Return as JSON array with format: {{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "answer": "A"}}"""

    result = call_ai_with_fallback(prompt, max_tokens=4000, is_json=True)
    
    if result['success']:
        try:
            questions_data = json.loads(result['content'])
            for q_data in questions_data[:20]:
                ExamQuestion.objects.create(
                    exam=exam,
                    question_text=q_data.get('question', ''),
                    options=q_data.get('options', {}),
                    correct_answer=q_data.get('answer', 'A')
                )
            exam.total_questions = len(questions_data[:20])
            exam.save()
        except:
            messages.error(request, 'Error generating exam. Please try again.')
            exam.delete()
            return redirect('courses:module_listing', course_id=module.course.id)
    else:
        messages.error(request, 'AI tutors are at capacity. Please try again later.')
        exam.delete()
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
