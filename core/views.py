from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Professional landing page for unauthenticated visitors"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


@login_required
def dashboard_view(request):
    """Main dashboard view with actual user statistics"""
    from courses.models import Course
    from quizzes.models import QuizAttempt

    # Get user's courses with prefetch to avoid N+1 queries
    user_courses = Course.objects.filter(user=request.user).prefetch_related('modules')

    # Get statistics
    courses_count = user_courses.count()
    quizzes_count = QuizAttempt.objects.filter(user=request.user, completed_at__isnull=False).count()

    return render(request, 'core/dashboard.html', {
        'referral_url': f"{request.scheme}://{request.get_host()}/join/{request.user.username}",
        'user_credits': request.user.tutor_credits,
        'user_daily_limit': request.user.daily_credit_limit,
        'courses_count': courses_count,
        'quizzes_count': quizzes_count,
        'user_courses': user_courses[:3],
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