from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from .models import Course, Module, CachedLesson
from .forms import CourseCreationForm
from core.utils.ai_module_generator import generate_course_modules
from core.services.curriculum import CurriculumService
from django.db import transaction
from django.http import JsonResponse
from quizzes.models import QuizAttempt
import bleach
import logging

logger = logging.getLogger(__name__)


class CourseDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user_courses = Course.objects.filter(user=request.user).select_related(
            'school_level', 'term', 'curriculum'
        ).order_by('-created_at')

        context = {
            'courses': user_courses,
            'title': 'My Akili Courses',
        }

        return render(request, 'courses/dashboard.html', context)


class CourseCreationView(LoginRequiredMixin, View):
    def get(self, request):
        form = CourseCreationForm()
        context = {
            'form': form,
            'title': 'Create New Course',
        }
        return render(request, 'courses/course_creation.html', context)

    def post(self, request):
        form = CourseCreationForm(request.POST)

        if form.is_valid():
            school_level = form.cleaned_data['school_level_obj']
            term = form.cleaned_data['term_obj']
            subject = form.cleaned_data['subject_obj']
            curriculum = form.cleaned_data['curriculum_obj']

            existing = Course.objects.filter(
                user=request.user,
                school_level=school_level,
                term=term,
                subject=subject.name
            ).exists()
            
            if existing:
                messages.info(request, "You already have this course.")
                return redirect('dashboard')

            try:
                with transaction.atomic():
                    if not request.user.deduct_credits(5):
                        messages.error(request, 'Insufficient credits. You need 5 credits to create a course.')
                        return render(request, 'courses/course_creation.html', {'form': form, 'title': 'Create New Course'})

                    new_course = Course.objects.create(
                        user=request.user,
                        subject=subject.name,
                        school_level=school_level,
                        term=term,
                        curriculum=curriculum,
                        exam_type=None
                    )

                    success = generate_course_modules(new_course)

                    if not success:
                        raise Exception("AI module generation failed.")

                messages.success(request, f'Course "{subject.name}" created successfully!')
                return redirect('dashboard')

            except Exception as e:
                logger.error(f"Course creation failed and rolled back: {e}")
                messages.error(request, 'Sorry, the AI tutor is busy. Please try again.')

        context = {
            'form': form,
            'title': 'Create New Course',
        }
        return render(request, 'courses/course_creation.html', context)


class ModuleListingView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, user=request.user)
        modules = list(course.modules.all().order_by('order'))

        # Prefetch all quiz attempts for this user and course's modules in a single query
        module_ids = [m.id for m in modules]
        all_attempts = QuizAttempt.objects.filter(
            user=request.user,
            module_id__in=module_ids
        ).select_related('module')

        # Build lookup dictionaries for O(1) access
        passed_modules = set()
        best_attempts = {}
        incomplete_quizzes = {}

        for attempt in all_attempts:
            mid = attempt.module_id
            if attempt.passed:
                passed_modules.add(mid)
            if attempt.completed_at:
                if mid not in best_attempts or attempt.score > best_attempts[mid].score:
                    best_attempts[mid] = attempt
            else:
                if mid not in incomplete_quizzes:
                    incomplete_quizzes[mid] = attempt

        # Build module order lookup
        module_by_order = {m.order: m for m in modules}

        modules_with_status = []
        for module in modules:
            is_locked = False
            lock_reason = ""

            if module.order > 1:
                previous_module = module_by_order.get(module.order - 1)
                if previous_module and previous_module.id not in passed_modules:
                    is_locked = True
                    passing_pct = getattr(settings, 'AKILI_QUIZ_PASSING_PERCENTAGE', 60)
                    lock_reason = f"Complete Module {previous_module.order} quiz with {passing_pct}% or higher to unlock"

            modules_with_status.append({
                'module': module,
                'is_locked': is_locked,
                'lock_reason': lock_reason,
                'best_attempt': best_attempts.get(module.id),
                'incomplete_quiz': incomplete_quizzes.get(module.id),
            })

        context = {
            'course': course,
            'modules_with_status': modules_with_status,
            'title': f'{course.display_name} - Modules',
        }
        return render(request, 'courses/module_listing.html', context)


class LessonDetailView(LoginRequiredMixin, View):
    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__user=request.user)

        if not module.lesson_content:
            lesson = self._generate_lesson(module)
        else:
            lesson = module.lesson_content
            if lesson.report_count > settings.AKILI_LESSON_REPORT_THRESHOLD:
                lesson.delete()
                lesson = self._generate_lesson(module)

        incomplete_quiz = QuizAttempt.objects.filter(
            user=request.user,
            module=module,
            completed_at__isnull=True
        ).first()

        best_attempt = QuizAttempt.objects.filter(
            user=request.user,
            module=module,
            completed_at__isnull=False
        ).order_by('-score').first()

        context = {
            'module': module,
            'lesson': lesson,
            'course': module.course,
            'title': module.title,
            'incomplete_quiz': incomplete_quiz,
            'best_attempt': best_attempt,
        }
        return render(request, 'courses/lesson_detail.html', context)

    def _generate_lesson(self, module):
        from core.utils.ai_fallback import call_ai_with_fallback, validate_ai_content
        import markdown

        course = module.course
        
        if course.school_level and course.term and course.curriculum:
            school_level = course.school_level
            term = course.term
            curriculum = course.curriculum
            
            previous_topics = CurriculumService.get_previous_topics(curriculum, module.topic.week if module.topic else term.weeks.first(), limit=3)
            previous_summary = ", ".join([t.title for t in previous_topics]) if previous_topics else "None"
            
            week_info = ""
            difficulty = "INTERMEDIATE"
            learning_objectives = ""
            
            if module.topic:
                week_info = f"Week {module.topic.week.week_number} ({module.topic.week.week_type})"
                difficulty = module.topic.difficulty_level
                learning_objectives = "\n".join(module.topic.learning_objectives) if module.topic.learning_objectives else ""
            
            prompt = f"""You are creating lesson content for Nigerian secondary school students.

Context:
- Class Level: {school_level.name} ({school_level.level_type})
- Subject: {course.subject}
- Term: {term.name} (Weeks {term.instructional_weeks} of instruction)
- {week_info}
- Topic: {module.syllabus_topic}
- Difficulty: {difficulty}
- Previous Topics: {previous_summary}

Nigerian Curriculum Alignment:
{learning_objectives}

INSTRUCTIONS:
1. Format your response in Markdown for better readability
2. Use **bold** for key terms, *italics* for emphasis
3. Use numbered lists for steps and bullet points for key points
4. Include practical examples to illustrate concepts
5. DO NOT include solutions to practice problems or exercises
6. If you include practice questions, only provide the questions without answers
7. Focus on explaining concepts clearly appropriate for {school_level.name} students

Generate a comprehensive lesson for Week {module.topic.week.week_number if module.topic else 'this'} of {term.name}.
Build on concepts from previous weeks. The difficulty should match {difficulty} level."""
        else:
            prompt = f"""Create a comprehensive lesson on the following topic for {course.exam_type or 'secondary school'} {course.subject}:

Topic: {module.syllabus_topic}
Module Title: {module.title}

IMPORTANT INSTRUCTIONS:
1. Format your response in Markdown for better readability
2. Use **bold** for key terms, *italics* for emphasis
3. Use numbered lists for steps and bullet points for key points
4. Include practical examples to illustrate concepts
5. DO NOT include solutions to practice problems or exercises
6. If you include practice questions, only provide the questions without answers
7. Focus on explaining concepts clearly for exam preparation

Provide a detailed, well-structured lesson covering all key concepts."""

        result = call_ai_with_fallback(prompt, max_tokens=2000, subject=course.subject)
        if not result['success']:
            content_markdown = "AI tutors are at full capacity. Please try again in 2-3 minutes."
            content_html = content_markdown
            is_validated = False
        else:
            content_markdown = result['content']
            raw_html = markdown.markdown(
                content_markdown,
                extensions=['extra', 'codehilite', 'tables', 'fenced_code']
            )
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'b', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'pre', 'code', 'blockquote', 'table', 'thead', 'tbody',
                'tr', 'th', 'td', 'a', 'div', 'span', 'hr', 'sub', 'sup'
            ]
            allowed_attrs = {
                'a': ['href', 'title'],
                'code': ['class'],
                'pre': ['class'],
                'div': ['class'],
                'span': ['class'],
                'table': ['class'],
                'th': ['colspan', 'rowspan'],
                'td': ['colspan', 'rowspan'],
            }
            allowed_protocols = ['http', 'https', 'mailto']
            content_html = bleach.clean(
                raw_html, 
                tags=allowed_tags, 
                attributes=allowed_attrs,
                protocols=allowed_protocols,
                strip=True
            )
            validation_result = validate_ai_content(content_markdown)
            is_validated = validation_result.strip().upper() == 'OK'
            if not is_validated:
                content_html = f"{content_html}<div class='mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg text-sm text-yellow-800 dark:text-yellow-200'><strong>Note:</strong> This content is under review.</div>"

        lesson = CachedLesson.objects.create(
            topic=module.syllabus_topic,
            content=content_html,
            syllabus_version="2025",
            is_validated=is_validated,
            requested_by=module.course.user
        )

        module.lesson_content = lesson
        module.save()

        return lesson


class AskTutorView(LoginRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__user=request.user)
        question = request.POST.get('question', '').strip()

        if not question:
            messages.error(request, 'Please enter a question.')
            return redirect('courses:lesson_detail', module_id=module_id)

        if not request.user.deduct_credits(1):
            messages.error(request, 'Insufficient credits. You need 1 credit to ask a question.')
            return redirect('courses:lesson_detail', module_id=module_id)

        from core.utils.ai_fallback import call_ai_with_fallback

        course = module.course
        context_info = ""
        if course.school_level and course.term:
            context_info = f"Class Level: {course.school_level.name}, Term: {course.term.name}"
        else:
            context_info = f"Exam Type: {course.exam_type}"
        
        prompt = f"""You are a tutor for {course.subject}.

{context_info}
Topic: {module.syllabus_topic}
Student Question: {question}

Provide a clear, helpful answer appropriate for the student's level."""

        result = call_ai_with_fallback(prompt, max_tokens=1000, subject=course.subject)
        
        if result['success']:
            messages.success(request, f"AI Tutor: {result['content']}")
        else:
            request.user.add_credits(1)
            messages.error(request, 'AI tutors are at capacity. Please try again later. Your credit has been refunded.')

        return redirect('courses:lesson_detail', module_id=module_id)


class ReportErrorView(LoginRequiredMixin, View):
    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__user=request.user)

        if module.lesson_content:
            module.lesson_content.report_count += 1
            module.lesson_content.save()
            messages.success(request, 'Error reported. Thank you for helping us improve!')

        return redirect('courses:lesson_detail', module_id=module_id)


class DeleteCourseView(LoginRequiredMixin, View):
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, user=request.user)
        course_name = course.display_name

        password = request.POST.get('password', '')
        if not password:
            messages.error(request, "Please enter your password to confirm course deletion.")
            return redirect('dashboard')

        if not request.user.check_password(password):
            messages.error(request, "Incorrect password. Course deletion cancelled.")
            return redirect('dashboard')

        course.delete()
        messages.success(request, f'Course "{course_name}" deleted successfully.')
        return redirect('dashboard')


class GetAvailableSubjectsView(LoginRequiredMixin, View):
    def get(self, request):
        school_level_id = request.GET.get('school_level')
        
        if school_level_id:
            try:
                subjects = CurriculumService.get_subjects_for_level_by_id(int(school_level_id))
                subjects_list = [{'id': s.id, 'name': s.name} for s in subjects]
                return JsonResponse({'subjects': subjects_list})
            except (ValueError, TypeError):
                return JsonResponse({'subjects': []})
        
        return JsonResponse({'subjects': []})


class TutorHubView(LoginRequiredMixin, View):
    """Global AI Tutor Hub - ask questions across all subjects"""
    
    def get(self, request):
        user_courses = Course.objects.filter(user=request.user).select_related(
            'school_level', 'term'
        ).prefetch_related('modules').order_by('-created_at')
        
        recent_modules = []
        for course in user_courses[:5]:
            for module in course.modules.all()[:3]:
                recent_modules.append({
                    'module': module,
                    'course': course,
                })
                if len(recent_modules) >= 6:
                    break
            if len(recent_modules) >= 6:
                break
        
        context = {
            'title': 'AI Tutor',
            'courses': user_courses,
            'recent_modules': recent_modules,
            'user_credits': request.user.tutor_credits,
        }
        return render(request, 'courses/tutor_hub.html', context)
    
    def post(self, request):
        module_id = request.POST.get('module_id')
        question = request.POST.get('question', '').strip()
        
        if not module_id:
            messages.error(request, 'Please select a topic to ask about.')
            return redirect('courses:tutor_hub')
        
        module = get_object_or_404(Module, id=module_id, course__user=request.user)
        
        if not question:
            messages.error(request, 'Please enter a question.')
            return redirect('courses:tutor_hub')
        
        if not request.user.deduct_credits(1):
            messages.error(request, 'Insufficient credits. You need 1 credit to ask a question.')
            return redirect('courses:tutor_hub')
        
        from core.utils.ai_fallback import call_ai_with_fallback
        
        course = module.course
        context_info = ""
        if course.school_level and course.term:
            context_info = f"Class Level: {course.school_level.name}, Term: {course.term.name}"
        else:
            context_info = f"Exam Type: {course.exam_type}"
        
        prompt = f"""You are a friendly and helpful AI tutor for Nigerian secondary school students studying {course.subject}.

{context_info}
Topic: {module.syllabus_topic}

Student's Question: {question}

Provide a clear, encouraging, and educational answer appropriate for the student's level. Use examples relevant to Nigerian students where possible. Format your response with clear sections if needed."""

        result = call_ai_with_fallback(prompt, max_tokens=1500, subject=course.subject)
        
        if result.get('success'):
            answer = bleach.clean(result.get('content', ''), tags=[], strip=True)
            context = {
                'title': 'AI Tutor Response',
                'question': question,
                'answer': result.get('content', ''),
                'module': module,
                'course': course,
            }
            return render(request, 'courses/tutor_response.html', context)
        else:
            messages.error(request, 'Sorry, I could not process your question. Please try again.')
            request.user.add_credits(1)
            return redirect('courses:tutor_hub')
