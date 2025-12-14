from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from .models import Course, Module, CachedLesson
from .forms import CourseCreationForm, LegacyCourseCreationForm
from core.utils.ai_module_generator import generate_course_modules
from core.services.curriculum import CurriculumService
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus
from django.db import transaction
from django.http import JsonResponse
import bleach


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
                print(f"Course creation failed and rolled back: {e}")
                messages.error(request, 'Sorry, the AI tutor is busy. Please try again.')

        context = {
            'form': form,
            'title': 'Create New Course',
        }
        return render(request, 'courses/course_creation.html', context)


class ModuleListingView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, user=request.user)
        modules = course.modules.all().order_by('order')

        modules_with_status = []
        for module in modules:
            is_locked = False
            lock_reason = ""

            if module.order > 1:
                previous_module = course.modules.filter(order=module.order - 1).first()
                if previous_module:
                    from quizzes.models import QuizAttempt
                    passed_previous = QuizAttempt.objects.filter(
                        user=request.user,
                        module=previous_module,
                        passed=True
                    ).exists()

                    if not passed_previous:
                        is_locked = True
                        lock_reason = f"Complete Module {previous_module.order} quiz with 60% or higher to unlock"

            from quizzes.models import QuizAttempt
            best_attempt = QuizAttempt.objects.filter(
                user=request.user,
                module=module,
                completed_at__isnull=False
            ).order_by('-score').first()

            incomplete_quiz = QuizAttempt.objects.filter(
                user=request.user,
                module=module,
                completed_at__isnull=True
            ).first()

            modules_with_status.append({
                'module': module,
                'is_locked': is_locked,
                'lock_reason': lock_reason,
                'best_attempt': best_attempt,
                'incomplete_quiz': incomplete_quiz,
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
            if lesson.report_count > 3:
                lesson.delete()
                lesson = self._generate_lesson(module)

        from quizzes.models import QuizAttempt
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

        if request.user.tutor_credits < 1:
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
            if request.user.deduct_credits(1):
                messages.success(request, f"AI Tutor: {result['content']}")
            else:
                messages.error(request, 'Insufficient credits.')
        else:
            messages.error(request, 'AI tutors are at capacity. Please try again later. No credits were deducted.')

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


class GetAvailableSubjectsView(View):
    def get(self, request):
        school_level_id = request.GET.get('school_level')
        exam_type = request.GET.get('exam_type', '')
        
        if school_level_id:
            try:
                subjects = CurriculumService.get_subjects_for_level_by_id(int(school_level_id))
                subjects_list = [{'id': s.id, 'name': s.name} for s in subjects]
                return JsonResponse({'subjects': subjects_list})
            except (ValueError, TypeError):
                return JsonResponse({'subjects': []})
        
        if exam_type:
            subjects = []
            if exam_type == 'JAMB':
                subjects = list(JAMBSyllabus.objects.all().values_list('subject', flat=True))
            elif exam_type == 'SSCE':
                subjects = list(SSCESyllabus.objects.all().values_list('subject', flat=True))
            elif exam_type == 'JSS':
                subjects = list(JSSSyllabus.objects.all().values_list('subject', flat=True))
            return JsonResponse({'subjects': subjects})
        
        return JsonResponse({'subjects': []})
