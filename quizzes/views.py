from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
import json
from django.db.models import Avg, Sum # <-- IMPORTED FOR STATS

from courses.models import Module
from .utils import generate_quiz_and_save
from .models import QuizAttempt


@login_required
def start_quiz_view(request, module_id):
    """View to trigger AI generation of a new quiz or view existing quiz."""
    module = get_object_or_404(Module, pk=module_id)

    if request.method != 'POST':
        messages.error(request, "Quiz generation requires a valid request.")
        return redirect('dashboard')

    # Check if user already has an incomplete quiz for this module
    existing_quiz = QuizAttempt.objects.filter(
        user=request.user,
        module=module,
        completed_at__isnull=True
    ).first()

    if existing_quiz:
        messages.info(request, f"Continuing your existing quiz for {module.title}")
        return redirect('quizzes:quiz_detail', quiz_id=existing_quiz.id)

    # Check if user wants to retake (has completed quiz)
    completed_quiz = QuizAttempt.objects.filter(
        user=request.user,
        module=module,
        completed_at__isnull=False
    ).order_by('-completed_at').first()

    if completed_quiz:
        # Allow retaking - generate new quiz
        messages.info(request, f"Generating a new quiz attempt for {module.title}")

    # Quizzes are now FREE - no credit check needed
    try:
        success, result_id_or_error = generate_quiz_and_save(module, request.user, num_questions=5)

        if success:
            messages.success(request, f"Quiz successfully generated for {module.title}!")
            return redirect('quizzes:quiz_detail', quiz_id=result_id_or_error)
        else:
            messages.error(request, 'Sorry, the AI tutor is busy. Please try again.')
            return redirect(reverse('courses:module_listing', kwargs={'course_id': module.course.id}))
    except Exception as e:
        print(f"Quiz generation error: {e}")
        messages.error(request, 'Sorry, the AI tutor is busy. Please try again.')
        return redirect(reverse('courses:module_listing', kwargs={'course_id': module.course.id}))


@login_required
def quiz_detail_view(request, quiz_id):
    """Displays the quiz questions and handles submission (scoring)."""

    # 1. Retrieve the quiz attempt
    quiz_attempt = get_object_or_404(
        QuizAttempt.objects.filter(user=request.user),
        pk=quiz_id
    )

    # Check if the quiz is already completed (read-only mode)
    is_completed = bool(quiz_attempt.completed_at)

    if request.method == 'POST' and not is_completed:
        # --- SCORING AND SUBMISSION LOGIC ---

        total_correct = 0
        user_answers = {}

        # Iterate over the questions stored in the JSONField
        for index, question in enumerate(quiz_attempt.questions_data):
            user_choice_str = request.POST.get(f'q_{index}')

            # CRITICAL FIX: Use .get() with None default for safety
            correct_index_value = question.get('correct_index')

            # Process the answer only if a choice was made AND the correct index exists in the data
            if user_choice_str and correct_index_value is not None:
                user_choice = int(user_choice_str)
                correct_index = int(correct_index_value) 

                is_correct = (user_choice == correct_index)

                if is_correct:
                    total_correct += 1

                # Store the user's choice
                user_answers[str(index)] = {'chosen': user_choice, 'is_correct': is_correct}
            else:
                # Store skipped or malformed question answer
                user_answers[str(index)] = {'chosen': -1, 'is_correct': False}

        # 2. Update QuizAttempt record
        quiz_attempt.score = total_correct
        quiz_attempt.total_questions = len(quiz_attempt.questions_data)
        quiz_attempt.completed_at = timezone.now() # Record completion time
        quiz_attempt.user_answers = user_answers

        # Set passed status based on 60% threshold
        quiz_attempt.passed = quiz_attempt.is_passing

        quiz_attempt.save()

        # Provide feedback on pass/fail status
        if quiz_attempt.passed:
            messages.success(request, f"Quiz submitted! You scored {total_correct} out of {quiz_attempt.total_questions} ({quiz_attempt.percentage}%) - PASSED! Next module unlocked.")
        else:
            messages.warning(request, f"Quiz submitted! You scored {total_correct} out of {quiz_attempt.total_questions} ({quiz_attempt.percentage}%). You need 60% to pass and unlock the next module.")
        return redirect('quizzes:quiz_detail', quiz_id=quiz_attempt.id)


    # --- GET REQUEST (Display Form/Results) ---

    if is_completed:
        template_name = 'quizzes/quiz_results.html'
    else:
        template_name = 'quizzes/quiz_form.html'

    context = {
        'quiz': quiz_attempt,
        'questions': quiz_attempt.questions_data, 
        'title': f"Quiz for {quiz_attempt.module.title}",
        'user_answers': quiz_attempt.user_answers if is_completed else None, 
    }

    return render(request, template_name, context)


@login_required
def quiz_history_view(request):
    """Displays a list of all completed quiz attempts."""

    # --- FIX: Filter for completed quizzes only ---
    completed_quizzes = QuizAttempt.objects.filter(
        user=request.user,
        completed_at__isnull=False
    ).order_by('-completed_at')

    # --- FIX: Calculate stats for the template ---
    stats = completed_quizzes.aggregate(
        total_s=Sum('score'),
        total_q=Sum('total_questions')
    )

    # Calculate average percentage
    if stats['total_q'] and stats['total_s'] is not None and stats['total_q'] > 0:
        average_score = (stats['total_s'] / stats['total_q']) * 100
    else:
        average_score = 0

    total_questions_answered = stats['total_q'] or 0

    context = {
        'quizzes': completed_quizzes, # <-- FIX: Changed 'history' to 'quizzes'
        'average_score': average_score,
        'total_questions': total_questions_answered,
        'title': 'Quiz History',
    }

    return render(request, 'quizzes/quiz_history.html', context)