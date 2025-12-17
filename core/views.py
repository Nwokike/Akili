from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Professional landing page for unauthenticated visitors"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


@login_required
def dashboard_view(request):
    """Main dashboard view with comprehensive statistics and quick actions"""
    from courses.models import Course, Module
    from quizzes.models import QuizAttempt
    from assessments.models import Grade, Notification, CourseExam, StudyPlan
    from django.db.models import Avg, Count, Max
    from datetime import datetime
    
    user_courses = Course.objects.filter(user=request.user).prefetch_related('modules').select_related('school_level', 'term')
    
    today_weekday = datetime.now().weekday()
    today_schedule = StudyPlan.objects.filter(user=request.user, day_of_week=today_weekday).select_related('course').order_by('start_time')
    
    courses_count = user_courses.count()
    quizzes_count = QuizAttempt.objects.filter(user=request.user, completed_at__isnull=False).count()
    
    grades = Grade.objects.filter(student=request.user)
    grade_stats = grades.aggregate(
        avg_total=Avg('total_score'),
        avg_ca=Avg('continuous_assessment_score'),
        avg_exam=Avg('exam_score'),
        count=Count('id')
    )
    
    overall_grade = grade_stats.get('avg_total') or 0
    
    recent_quizzes = QuizAttempt.objects.filter(
        user=request.user,
        completed_at__isnull=False
    ).select_related('module__course').order_by('-completed_at')[:5]
    
    recent_exams = CourseExam.objects.filter(
        user=request.user,
        completed_at__isnull=False
    ).select_related('course').order_by('-completed_at')[:3]
    
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    continue_learning = []
    for course in user_courses[:3]:
        last_attempt = QuizAttempt.objects.filter(
            user=request.user,
            module__course=course,
            completed_at__isnull=False
        ).order_by('-completed_at').first()
        
        if last_attempt:
            next_module = Module.objects.filter(
                course=course,
                order__gt=last_attempt.module.order
            ).order_by('order').first()
            if next_module:
                continue_learning.append({
                    'course': course,
                    'module': next_module,
                    'action': 'Continue'
                })
        else:
            first_module = course.modules.order_by('order').first()
            if first_module:
                continue_learning.append({
                    'course': course,
                    'module': first_module,
                    'action': 'Start'
                })
    
    has_parent_profile = hasattr(request.user, 'parent_profile')
    
    return render(request, 'core/dashboard.html', {
        'referral_url': f"{request.scheme}://{request.get_host()}/join/{request.user.username}",
        'user_credits': request.user.tutor_credits,
        'user_daily_limit': request.user.daily_credit_limit,
        'courses_count': courses_count,
        'quizzes_count': quizzes_count,
        'user_courses': user_courses[:6],
        'overall_grade': round(overall_grade, 1),
        'grade_stats': grade_stats,
        'recent_quizzes': recent_quizzes,
        'recent_exams': recent_exams,
        'unread_notifications': unread_notifications,
        'continue_learning': continue_learning[:3],
        'has_parent_profile': has_parent_profile,
        'today_schedule': today_schedule[:4],
    })


def privacy_view(request):
    """Privacy policy page"""
    return render(request, 'legal/privacy.html')


def terms_view(request):
    """Terms of service page"""
    return render(request, 'legal/terms.html')


def about_view(request):
    """About page"""
    return render(request, 'legal/about.html')


def error_404_view(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)


def error_500_view(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)


def error_403_view(request, exception):
    """Custom 403 error page"""
    return render(request, 'errors/403.html', status=403)