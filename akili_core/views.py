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
    """Mock exam center - Developer 2 will implement"""
    return render(request, 'exams/exam_center.html')


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
