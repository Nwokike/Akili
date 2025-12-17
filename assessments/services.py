"""
Grade synchronization services for connecting quizzes to the assessment system.
"""
from decimal import Decimal
from django.db.models import Avg, Max
from django.conf import settings


def update_grade_from_quiz(quiz_attempt):
    """
    Update or create a Grade record based on completed quiz attempts.
    
    The continuous assessment (CA) score is calculated as the average of best quiz scores
    for each module in the course, scaled to 40% of the total grade.
    
    Args:
        quiz_attempt: A QuizAttempt instance that has been completed
    
    Returns:
        Grade instance or None if the course doesn't have curriculum/term
    """
    from assessments.models import Grade
    from quizzes.models import QuizAttempt
    
    course = quiz_attempt.module.course
    user = quiz_attempt.user
    
    if not course.curriculum or not course.term:
        return None
    
    grade, created = Grade.objects.get_or_create(
        student=user,
        curriculum=course.curriculum,
        term=course.term,
        defaults={
            'continuous_assessment_score': Decimal('0'),
            'exam_score': Decimal('0'),
        }
    )
    
    all_modules = course.modules.all()
    module_count = all_modules.count()
    
    if module_count == 0:
        return grade
    
    total_best_percentage = Decimal('0')
    modules_with_attempts = 0
    
    for module in all_modules:
        best_attempt = QuizAttempt.objects.filter(
            user=user,
            module=module,
            completed_at__isnull=False
        ).order_by('-score').first()
        
        if best_attempt:
            modules_with_attempts += 1
            total_best_percentage += Decimal(str(best_attempt.percentage))
    
    if modules_with_attempts > 0:
        average_percentage = total_best_percentage / modules_with_attempts
        ca_max = Decimal(str(getattr(settings, 'AKILI_CA_MAX_SCORE', 40)))
        ca_score = (average_percentage / 100) * ca_max
        grade.continuous_assessment_score = round(ca_score, 2)
    
    grade.compute_grade()
    
    return grade


def backfill_grades_for_user(user):
    """
    Backfill grades for all completed quizzes for a user.
    
    Args:
        user: CustomUser instance
    
    Returns:
        List of Grade instances created/updated
    """
    from quizzes.models import QuizAttempt
    from courses.models import Course
    
    courses_with_quizzes = Course.objects.filter(
        modules__quiz_attempts__user=user,
        modules__quiz_attempts__completed_at__isnull=False,
        curriculum__isnull=False,
        term__isnull=False
    ).distinct()
    
    grades = []
    for course in courses_with_quizzes:
        first_attempt = QuizAttempt.objects.filter(
            user=user,
            module__course=course,
            completed_at__isnull=False
        ).first()
        
        if first_attempt:
            grade = update_grade_from_quiz(first_attempt)
            if grade:
                grades.append(grade)
    
    return grades


def backfill_all_grades():
    """
    Backfill grades for all users with completed quizzes.
    Used by management command.
    
    Returns:
        Tuple of (total_grades_created, total_users_processed)
    """
    from quizzes.models import QuizAttempt
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    users_with_quizzes = User.objects.filter(
        quiz_attempts__completed_at__isnull=False
    ).distinct()
    
    total_grades = 0
    total_users = 0
    
    for user in users_with_quizzes:
        grades = backfill_grades_for_user(user)
        total_grades += len(grades)
        total_users += 1
    
    return total_grades, total_users
