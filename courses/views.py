from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from .models import Course, Module, CachedLesson
from .forms import CourseCreationForm
from core.utils.ai_module_generator import generate_course_modules
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus 


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
                messages.info(request, "You already have this course.")
                return redirect('dashboard') 
            
            # 2. Check Credits (5 credits per course creation)
            if not request.user.deduct_credits(5):
                messages.error(request, 'Insufficient credits. You need 5 credits to create a course.')
                return render(request, 'courses/course_creation.html', {'form': form, 'title': 'Create New Course'})
            
            # 3. Create the Course instance
            new_course = Course.objects.create(
                user=request.user,
                exam_type=exam_type,
                subject=subject,
            )
            
            # 4. Generate modules using AI
            success = generate_course_modules(new_course)
            if not success:
                messages.warning(request, 'Course created but AI module generation is still processing. Please refresh in a moment.')
            else:
                messages.success(request, f'Course created successfully with 15 modules!')
            
            return redirect('dashboard')
            
        context = {
            'form': form,
            'title': 'Create New Course',
        }
        return render(request, 'courses/course_creation.html', context)

class ModuleListingView(LoginRequiredMixin, View):
    """
    Displays all modules for a specific course with locking system
    """
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, user=request.user)
        modules = course.modules.all().order_by('order')
        
        # Add lock status to each module
        modules_with_status = []
        for module in modules:
            # Check if user has passed the previous module's quiz
            is_locked = False
            lock_reason = ""
            
            if module.order > 1:
                # Get the previous module
                previous_module = course.modules.filter(order=module.order - 1).first()
                if previous_module:
                    # Check if user has passed the previous module's quiz
                    from quizzes.models import QuizAttempt
                    passed_previous = QuizAttempt.objects.filter(
                        user=request.user,
                        module=previous_module,
                        passed=True
                    ).exists()
                    
                    if not passed_previous:
                        is_locked = True
                        lock_reason = f"Complete Module {previous_module.order} quiz with 60% or higher to unlock"
            
            # Get best quiz attempt for this module
            from quizzes.models import QuizAttempt
            best_attempt = QuizAttempt.objects.filter(
                user=request.user,
                module=module
            ).order_by('-score').first()
            
            modules_with_status.append({
                'module': module,
                'is_locked': is_locked,
                'lock_reason': lock_reason,
                'best_attempt': best_attempt,
            })
        
        context = {
            'course': course,
            'modules_with_status': modules_with_status,
            'title': f'{course.exam_type} {course.subject} - Modules',
        }
        return render(request, 'courses/module_listing.html', context)


class LessonDetailView(LoginRequiredMixin, View):
    """
    Displays lesson content for a module with two-pass AI validation
    """
    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__user=request.user)
        
        # Generate or retrieve cached lesson
        if not module.lesson_content:
            lesson = self._generate_lesson(module)
        else:
            lesson = module.lesson_content
            # Check if lesson needs regeneration (reported >3 times)
            if lesson.report_count > 3:
                lesson.delete()
                lesson = self._generate_lesson(module)
        
        context = {
            'module': module,
            'lesson': lesson,
            'course': module.course,
            'title': module.title,
        }
        return render(request, 'courses/lesson_detail.html', context)
    
    def _generate_lesson(self, module):
        """Generate lesson content with two-pass validation"""
        from core.utils.ai_fallback import call_ai_with_fallback, validate_ai_content
        
        # Pass 1: Generate lesson content
        prompt = f"""Create a comprehensive lesson on the following topic for {module.course.exam_type} {module.course.subject}:

Topic: {module.syllabus_topic}
Module Title: {module.title}

Provide a detailed explanation with examples, covering all key concepts."""
        
        result = call_ai_with_fallback(prompt, max_tokens=2000)
        if not result['success']:
            content = "AI tutors are at full capacity. Please try again in 2-3 minutes."
            is_validated = False
        else:
            content = result['content']
            # Pass 2: Validate the content
            validation_result = validate_ai_content(content)
            is_validated = validation_result.strip().upper() == 'OK'
            if not is_validated:
                content = f"{content}\n\n**Note:** This content is under review."
        
        # Create CachedLesson
        lesson = CachedLesson.objects.create(
            topic=module.syllabus_topic,
            content=content,
            syllabus_version="2025",
            is_validated=is_validated,
            requested_by=module.course.user
        )
        
        # Link to module
        module.lesson_content = lesson
        module.save()
        
        return lesson


class AskTutorView(LoginRequiredMixin, View):
    """
    Handle follow-up questions (costs 1 credit)
    """
    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__user=request.user)
        question = request.POST.get('question', '').strip()
        
        if not question:
            messages.error(request, 'Please enter a question.')
            return redirect('courses:lesson_detail', module_id=module_id)
        
        # Deduct 1 credit
        if not request.user.deduct_credits(1):
            messages.error(request, 'Insufficient credits. You need 1 credit to ask a question.')
            return redirect('courses:lesson_detail', module_id=module_id)
        
        # Get AI response
        from core.utils.ai_fallback import call_ai_with_fallback
        prompt = f"""You are a tutor for {module.course.exam_type} {module.course.subject}.

Topic: {module.syllabus_topic}
Student Question: {question}

Provide a clear, helpful answer."""
        
        result = call_ai_with_fallback(prompt, max_tokens=1000)
        if result['success']:
            messages.success(request, f"AI Tutor: {result['content']}")
        else:
            messages.error(request, 'AI tutors are at capacity. Please try again later.')
        
        return redirect('courses:lesson_detail', module_id=module_id)


class ReportErrorView(LoginRequiredMixin, View):
    """
    Report error in lesson (increment report_count)
    """
    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__user=request.user)
        
        if module.lesson_content:
            module.lesson_content.report_count += 1
            module.lesson_content.save()
            messages.success(request, 'Error reported. Thank you for helping us improve!')
        
        return redirect('courses:lesson_detail', module_id=module_id)


class DeleteCourseView(LoginRequiredMixin, View):
    """
    Delete a course with confirmation
    """
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, user=request.user)
        course_name = f"{course.exam_type} {course.subject}"
        course.delete()
        messages.success(request, f'Course "{course_name}" deleted successfully.')
        return redirect('dashboard')


from django.http import JsonResponse

class GetAvailableSubjectsView(View):
    """
    AJAX endpoint to fetch available subjects for a given exam type
    """
    def get(self, request):
        exam_type = request.GET.get('exam_type', '')
        subjects = []
        
        if exam_type == 'JAMB':
            subjects = list(JAMBSyllabus.objects.all().values_list('subject', flat=True))
        elif exam_type == 'SSCE':
            subjects = list(SSCESyllabus.objects.all().values_list('subject', flat=True))
        elif exam_type == 'JSS':
            subjects = list(JSSSyllabus.objects.all().values_list('subject', flat=True))
        
        return JsonResponse({'subjects': subjects})
