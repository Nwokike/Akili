from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Exam, ExamQuestion
from quizzes.models import Question


@login_required
def start_exam(request, module_id):
    """
    Generate a mock exam from quizzes related to a module.
    """
    from courses.models import Module
    module = get_object_or_404(Module, id=module_id)

    exam = Exam.objects.create(
        user=request.user,
        module=module,
        title=f"{module.title} Mock Exam"
    )

    # Pull 20 random questions from quizzes
    questions = Question.objects.filter(module=module).order_by("?")[:20]
    for q in questions:
        ExamQuestion.objects.create(
            exam=exam,
            question_text=q.questions_data.get("text", ""),
            options=q.questions_data.get("options", {}),
            correct_answer=q.questions_data.get("answer", "")
        )

    exam.total_questions = len(questions)
    exam.save()

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
