from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count
from .models import (
    Assessment, AssessmentSubmission, Grade, ProgressReport,
    TeacherProfile, TeacherClass, Assignment, AssignmentSubmission,
    ParentProfile, Notification
)


@login_required
def assessments_list(request):
    """6.1: List available assessments for student"""
    assessments = Assessment.objects.filter(
        status='PUBLISHED'
    ).select_related('curriculum__subject', 'curriculum__school_level', 'week')
    
    my_submissions = AssessmentSubmission.objects.filter(
        student=request.user
    ).values_list('assessment_id', flat=True)
    
    context = {
        'assessments': assessments,
        'my_submissions': list(my_submissions),
    }
    return render(request, 'assessments/assessments_list.html', context)


@login_required
def assessment_detail(request, pk):
    """6.1: View and take assessment"""
    assessment = get_object_or_404(
        Assessment.objects.select_related('curriculum__subject', 'created_by'),
        pk=pk, status='PUBLISHED'
    )
    
    submission, created = AssessmentSubmission.objects.get_or_create(
        assessment=assessment,
        student=request.user,
        defaults={'status': 'IN_PROGRESS'}
    )
    
    if request.method == 'POST' and submission.status != 'GRADED':
        answers = {}
        for question in assessment.questions.all():
            answer = request.POST.get(f'question_{question.id}')
            if answer:
                answers[str(question.id)] = answer
        
        submission.answers = answers
        submission.status = 'SUBMITTED'
        submission.submitted_at = timezone.now()
        
        total_score = 0
        for question in assessment.questions.all():
            if answers.get(str(question.id)) == question.correct_answer:
                total_score += question.marks
        
        submission.score = total_score
        submission.status = 'GRADED'
        submission.graded_at = timezone.now()
        submission.save()
        
        messages.success(request, f'Assessment submitted! Your score: {total_score}/{assessment.total_marks}')
        return redirect('assessments:assessment_result', pk=assessment.pk)
    
    context = {
        'assessment': assessment,
        'questions': assessment.questions.all().order_by('order'),
        'submission': submission,
    }
    return render(request, 'assessments/assessment_detail.html', context)


@login_required
def assessment_result(request, pk):
    """6.1: View assessment results"""
    assessment = get_object_or_404(Assessment, pk=pk)
    submission = get_object_or_404(
        AssessmentSubmission,
        assessment=assessment,
        student=request.user
    )
    
    context = {
        'assessment': assessment,
        'submission': submission,
        'questions': assessment.questions.all().order_by('order'),
    }
    return render(request, 'assessments/assessment_result.html', context)


@login_required
def my_grades(request):
    """6.1: View student grades with quiz performance breakdown"""
    from courses.models import Course
    from quizzes.models import QuizAttempt
    
    grades = Grade.objects.filter(
        student=request.user
    ).select_related('curriculum__subject', 'curriculum__school_level', 'term')
    
    courses = Course.objects.filter(
        user=request.user,
        curriculum__isnull=False,
        term__isnull=False
    ).select_related('curriculum__subject', 'school_level', 'term').prefetch_related('modules')
    
    course_stats = []
    for course in courses:
        modules = course.modules.all()
        module_count = modules.count()
        
        completed_modules = 0
        total_best_percentage = 0
        
        for module in modules:
            attempts = QuizAttempt.objects.filter(
                user=request.user,
                module=module,
                completed_at__isnull=False
            )
            if attempts.exists():
                best = max(attempts, key=lambda a: a.percentage)
                completed_modules += 1
                total_best_percentage += best.percentage
        
        avg_score = total_best_percentage / completed_modules if completed_modules > 0 else 0
        progress = (completed_modules / module_count * 100) if module_count > 0 else 0
        
        course_grade = grades.filter(
            curriculum=course.curriculum,
            term=course.term
        ).first()
        
        course_stats.append({
            'course': course,
            'module_count': module_count,
            'completed_modules': completed_modules,
            'progress': round(progress),
            'average_score': round(avg_score, 1),
            'grade': course_grade,
            'mock_exam_ready': completed_modules >= max(1, module_count // 2),
        })
    
    context = {
        'grades': grades,
        'course_stats': course_stats,
    }
    return render(request, 'assessments/my_grades.html', context)


@login_required
def progress_report_view(request, pk):
    """6.1: View progress report"""
    report = get_object_or_404(
        ProgressReport.objects.select_related(
            'academic_session', 'term', 'school_level'
        ),
        pk=pk,
        student=request.user
    )
    
    grades = Grade.objects.filter(
        student=request.user,
        term=report.term
    ).select_related('curriculum__subject')
    
    context = {
        'report': report,
        'grades': grades,
    }
    return render(request, 'assessments/progress_report.html', context)


@login_required
def teacher_dashboard(request):
    """6.2: Teacher dashboard"""
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'You are not registered as a teacher.')
        return redirect('core:dashboard')
    
    classes = TeacherClass.objects.filter(
        teacher=teacher
    ).select_related('school_level', 'subject', 'academic_session')
    
    assignments = Assignment.objects.filter(
        teacher_class__teacher=teacher
    ).order_by('-due_date')[:5]
    
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__teacher_class__teacher=teacher,
        status='SUBMITTED'
    ).count()
    
    context = {
        'teacher': teacher,
        'classes': classes,
        'recent_assignments': assignments,
        'pending_submissions': pending_submissions,
    }
    return render(request, 'assessments/teacher_dashboard.html', context)


@login_required
def class_detail(request, pk):
    """6.2: View class details and students"""
    teacher_class = get_object_or_404(
        TeacherClass.objects.select_related('teacher', 'school_level', 'subject'),
        pk=pk,
        teacher__user=request.user
    )
    
    students = teacher_class.students.all()
    assignments = teacher_class.assignments.all().order_by('-due_date')
    
    context = {
        'teacher_class': teacher_class,
        'students': students,
        'assignments': assignments,
    }
    return render(request, 'assessments/class_detail.html', context)


@login_required
def class_analytics(request, pk):
    """6.2: Class performance analytics"""
    teacher_class = get_object_or_404(
        TeacherClass,
        pk=pk,
        teacher__user=request.user
    )
    
    submissions = AssignmentSubmission.objects.filter(
        assignment__teacher_class=teacher_class,
        status='GRADED'
    )
    
    avg_score = submissions.aggregate(avg=Avg('score'))['avg'] or 0
    submission_count = submissions.count()
    
    student_performance = []
    for student in teacher_class.students.all():
        student_subs = submissions.filter(student=student)
        student_avg = student_subs.aggregate(avg=Avg('score'))['avg'] or 0
        student_performance.append({
            'student': student,
            'average_score': round(student_avg, 2),
            'submissions': student_subs.count(),
        })
    
    context = {
        'teacher_class': teacher_class,
        'average_score': round(avg_score, 2),
        'total_submissions': submission_count,
        'student_performance': student_performance,
    }
    return render(request, 'assessments/class_analytics.html', context)


@login_required
def parent_dashboard(request):
    """6.3: Parent dashboard"""
    try:
        parent = request.user.parent_profile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'You are not registered as a parent.')
        return redirect('core:dashboard')
    
    children = parent.children.all()
    child_ids = list(children.values_list('id', flat=True))
    
    all_grades = Grade.objects.filter(
        student_id__in=child_ids
    ).select_related('curriculum__subject', 'student').order_by('-id')
    
    all_reports = ProgressReport.objects.filter(
        student_id__in=child_ids
    ).select_related('student').order_by('-generated_at')
    
    grades_by_child = {}
    for grade in all_grades:
        if grade.student_id not in grades_by_child:
            grades_by_child[grade.student_id] = []
        if len(grades_by_child[grade.student_id]) < 5:
            grades_by_child[grade.student_id].append(grade)
    
    reports_by_child = {}
    for report in all_reports:
        if report.student_id not in reports_by_child:
            reports_by_child[report.student_id] = report
    
    children_data = []
    for child in children:
        children_data.append({
            'child': child,
            'recent_grades': grades_by_child.get(child.id, []),
            'latest_report': reports_by_child.get(child.id),
        })
    
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    )[:10]
    
    context = {
        'parent': parent,
        'children_data': children_data,
        'notifications': notifications,
    }
    return render(request, 'assessments/parent_dashboard.html', context)


@login_required
def child_progress(request, child_id):
    """6.3: View child's progress"""
    try:
        parent = request.user.parent_profile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'You are not registered as a parent.')
        return redirect('core:dashboard')
    
    child = get_object_or_404(parent.children, pk=child_id)
    
    grades = Grade.objects.filter(
        student=child
    ).select_related('curriculum__subject', 'term')
    
    reports = ProgressReport.objects.filter(
        student=child
    ).select_related('academic_session', 'term', 'school_level')
    
    context = {
        'child': child,
        'grades': grades,
        'reports': reports,
    }
    return render(request, 'assessments/child_progress.html', context)


@login_required
def notifications_list(request):
    """6.3: View all notifications"""
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'assessments/notifications.html', context)


@login_required
def mark_notification_read(request, pk):
    """6.3: Mark notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if notification.link:
        return redirect(notification.link)
    return redirect('assessments:notifications')


@login_required
def mark_all_notifications_read(request):
    """6.3: Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('assessments:notifications')


@login_required
def parent_payments(request):
    """6.3: Parent Portal - Payment management for children"""
    try:
        parent = request.user.parent_profile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'You are not registered as a parent.')
        return redirect('core:dashboard')
    
    from payments.models import Payment
    
    parent_payments = Payment.objects.filter(
        user=request.user
    ).order_by('-created_at')[:20]
    
    children = parent.children.all()
    children_credits = []
    for child in children:
        children_credits.append({
            'child': child,
            'credits': child.tutor_credits,
        })
    
    context = {
        'parent': parent,
        'payments': parent_payments,
        'children_credits': children_credits,
        'parent_credits': request.user.tutor_credits,
    }
    return render(request, 'assessments/parent_payments.html', context)


@login_required
def start_course_exam(request, course_id):
    """Start a new course-wide mock exam"""
    from courses.models import Course
    from .models import CourseExam
    from .exam_utils import generate_exam_and_save
    
    course = get_object_or_404(Course, pk=course_id, user=request.user)
    
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('courses:module_listing', course_id=course_id)
    
    existing_exam = CourseExam.objects.filter(
        user=request.user,
        course=course,
        completed_at__isnull=True
    ).first()
    
    if existing_exam:
        messages.info(request, "Continuing your existing exam.")
        return redirect('assessments:course_exam_detail', exam_id=existing_exam.id)
    
    modules_count = course.modules.count()
    if modules_count < 1:
        messages.error(request, "This course has no modules to generate an exam from.")
        return redirect('courses:module_listing', course_id=course_id)
    
    success, result = generate_exam_and_save(course, request.user, num_questions=20)
    
    if success:
        messages.success(request, f"Mock exam generated for {course.subject}!")
        return redirect('assessments:course_exam_detail', exam_id=result)
    else:
        messages.error(request, "Failed to generate exam. Please try again.")
        return redirect('courses:module_listing', course_id=course_id)


@login_required
def course_exam_detail(request, exam_id):
    """View and submit a course mock exam"""
    from .models import CourseExam
    from .services import update_grade_from_exam
    from django.utils import timezone
    
    exam = get_object_or_404(
        CourseExam.objects.filter(user=request.user),
        pk=exam_id
    )
    
    is_completed = bool(exam.completed_at)
    
    if request.method == 'POST' and not is_completed:
        total_correct = 0
        user_answers = {}
        
        for index, question in enumerate(exam.questions_data):
            user_choice_str = request.POST.get(f'q_{index}')
            correct_index_value = question.get('correct_index')
            
            if user_choice_str and correct_index_value is not None:
                user_choice = int(user_choice_str)
                correct_index = int(correct_index_value)
                is_correct = (user_choice == correct_index)
                
                if is_correct:
                    total_correct += 1
                
                user_answers[str(index)] = {'chosen': user_choice, 'is_correct': is_correct}
            else:
                user_answers[str(index)] = {'chosen': -1, 'is_correct': False}
        
        exam.score = total_correct
        exam.completed_at = timezone.now()
        exam.user_answers = user_answers
        exam.passed = exam.is_passing
        exam.save()
        
        try:
            update_grade_from_exam(exam)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to update grade from exam: {e}")
        
        if exam.passed:
            messages.success(request, f"Exam completed! You scored {total_correct}/{exam.total_questions} ({exam.percentage}%) - PASSED!")
        else:
            messages.warning(request, f"Exam completed! You scored {total_correct}/{exam.total_questions} ({exam.percentage}%). You need 50% to pass.")
        
        return redirect('assessments:course_exam_detail', exam_id=exam.id)
    
    if is_completed:
        template_name = 'assessments/course_exam_result.html'
    else:
        template_name = 'assessments/course_exam_form.html'
    
    context = {
        'exam': exam,
        'questions': exam.questions_data,
        'title': f"Mock Exam: {exam.course.subject}",
        'user_answers': exam.user_answers if is_completed else None,
    }
    
    return render(request, template_name, context)
