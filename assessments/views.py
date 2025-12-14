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
    """6.1: View student grades"""
    grades = Grade.objects.filter(
        student=request.user
    ).select_related('curriculum__subject', 'curriculum__school_level', 'term')
    
    context = {
        'grades': grades,
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
