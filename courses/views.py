from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .models import Course, Module, CachedLesson
from .forms import CourseCreationForm # You will create this form next

# Assume the Akili project has a utility to check credits
# from core.utils import check_tutor_credits 


class CourseDashboardView(LoginRequiredMixin, View):
    """
    Developer 1 Task: Displays a list of all courses personalized for the logged-in user.
    """
    def get(self, request):
        # Retrieve all courses belonging to the current user
        user_courses = Course.objects.filter(user=request.user).order_by('-created_at')
        
        # Example of contextual data you might need:
        # has_credits = check_tutor_credits(request.user) # Check utility for credit system
        
        context = {
            'courses': user_courses,
            'title': 'My Akili Courses',
            # 'has_credits': has_credits, 
        }
        
        return render(request, 'courses/dashboard.html', context)


class CourseCreationView(LoginRequiredMixin, View):
    """
    Developer 1 Task: Handles the form submission to create a new personalized course.
    This involves selecting exam_type and subject, then using AI to generate modules.
    """
    def get(self, request):
        # Display the form to select exam type and subject
        form = CourseCreationForm()
        context = {
            'form': form,
            'title': 'Create New Course',
        }
        return render(request, 'courses/course_creation.html', context)
        
    def post(self, request):
        form = CourseCreationForm(request.POST)
        
        if form.is_valid():
            exam_type = form.cleaned_data['exam_type']
            subject = form.cleaned_data['subject']
            
            # 1. Check if the user already has this exact course
            if Course.objects.filter(user=request.user, exam_type=exam_type, subject=subject).exists():
                # Prevent duplicates and redirect to the dashboard
                return redirect(reverse('courses:dashboard')) 
            
            # 2. Check Credits (Essential for Akili's business logic)
            # if not check_tutor_credits(request.user, amount=5): # Assume 5 credits per course
            #     # Handle insufficient credits gracefully
            #     return render(request, 'courses/course_creation.html', {'form': form, 'error': 'Insufficient credits.'})
            
            # 3. Create the Course instance (The modules are generated later)
            new_course = Course.objects.create(
                user=request.user,
                exam_type=exam_type,
                subject=subject,
            )
            
            # 4. Trigger AI Module Generation (You'll implement this complex logic separately)
            # from core.utils.ai_fallback import trigger_module_generation
            # trigger_module_generation(new_course) 
            
            return redirect(reverse('courses:dashboard')) # Go back to dashboard after creation
            
        context = {
            'form': form,
            'title': 'Create New Course',
        }
        return render(request, 'courses/course_creation.html', context)

# You will add more views here later, like LessonDetailView
