from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Professional landing page for unauthenticated visitors"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


@login_required
def dashboard_view(request):
    """Main dashboard view"""
    return render(request, 'core/dashboard.html', {
        'referral_url': f"{request.scheme}://{request.get_host()}/join/{request.user.username}"
    })


@login_required
def exam_center_view(request):
    """Practice exam center with clear user guidance"""
    from exams.models import Exam
    from courses.models import Course
    
    # Get user's recent exams
    recent_exams = Exam.objects.filter(user=request.user).select_related('module__course').order_by('-created_at')[:10]
    
    # Get user's courses with modules
    user_courses = Course.objects.filter(user=request.user).prefetch_related('modules').order_by('-created_at')
    
    context = {
        'recent_exams': recent_exams,
        'user_courses': user_courses,
        'has_courses': user_courses.exists(),
    }
    
    return render(request, 'exams/exam_center.html', context)


@login_required
def profile_view(request):
    """User profile - Developer 1 will implement"""
    return render(request, 'profiles/profile.html')


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
