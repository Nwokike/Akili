from django.db import models
from django.conf import settings


class Assessment(models.Model):
    """6.1: Continuous Assessment - Weekly/Monthly tests"""
    ASSESSMENT_TYPE_CHOICES = [
        ('WEEKLY', 'Weekly Test'),
        ('MONTHLY', 'Monthly Test'),
        ('MIDTERM', 'Mid-Term Exam'),
        ('TERMINAL', 'Terminal Exam'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
    ]
    
    title = models.CharField(max_length=255)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES)
    curriculum = models.ForeignKey('curriculum.SubjectCurriculum', on_delete=models.CASCADE, related_name='assessments')
    week = models.ForeignKey('curriculum.Week', on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_assessments')
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=50)
    duration_minutes = models.IntegerField(default=60)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assessments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_assessment_type_display()})"


class AssessmentQuestion(models.Model):
    """Questions for assessments"""
    QUESTION_TYPE_CHOICES = [
        ('MCQ', 'Multiple Choice'),
        ('SHORT', 'Short Answer'),
        ('ESSAY', 'Essay'),
        ('TRUE_FALSE', 'True/False'),
    ]
    
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='MCQ')
    options = models.JSONField(default=dict, blank=True, help_text="For MCQ: {A: option1, B: option2...}")
    correct_answer = models.TextField()
    marks = models.IntegerField(default=1)
    order = models.IntegerField(default=1)
    explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'assessment_questions'
        ordering = ['assessment', 'order']

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class AssessmentSubmission(models.Model):
    """Student submissions for assessments"""
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('GRADED', 'Graded'),
    ]
    
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assessment_submissions')
    answers = models.JSONField(default=dict, help_text="{question_id: answer}")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    feedback = models.TextField(blank=True)

    class Meta:
        db_table = 'assessment_submissions'
        unique_together = ['assessment', 'student']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student} - {self.assessment.title}"

    @property
    def percentage(self):
        if self.score is not None and self.assessment.total_marks:
            return round((float(self.score) / self.assessment.total_marks) * 100, 2)
        return 0

    @property
    def is_passing(self):
        return self.score is not None and self.score >= self.assessment.passing_marks


class Grade(models.Model):
    """6.1: Grade computation - Term grades for students"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='grades')
    curriculum = models.ForeignKey('curriculum.SubjectCurriculum', on_delete=models.CASCADE, related_name='grades')
    term = models.ForeignKey('curriculum.Term', on_delete=models.CASCADE, related_name='grades')
    continuous_assessment_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="CA Score (usually 40%)")
    exam_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Exam Score (usually 60%)")
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_letter = models.CharField(max_length=2, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    remarks = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'grades'
        unique_together = ['student', 'curriculum', 'term']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.curriculum.subject.name}: {self.grade_letter}"

    def compute_grade(self):
        """Compute grade letter and points based on total score"""
        self.total_score = self.continuous_assessment_score + self.exam_score
        
        if self.total_score >= 70:
            self.grade_letter = 'A'
            self.grade_point = 4.0
            self.remarks = 'Excellent'
        elif self.total_score >= 60:
            self.grade_letter = 'B'
            self.grade_point = 3.0
            self.remarks = 'Very Good'
        elif self.total_score >= 50:
            self.grade_letter = 'C'
            self.grade_point = 2.0
            self.remarks = 'Good'
        elif self.total_score >= 45:
            self.grade_letter = 'D'
            self.grade_point = 1.0
            self.remarks = 'Fair'
        elif self.total_score >= 40:
            self.grade_letter = 'E'
            self.grade_point = 0.5
            self.remarks = 'Pass'
        else:
            self.grade_letter = 'F'
            self.grade_point = 0.0
            self.remarks = 'Fail'
        
        self.save()


class ProgressReport(models.Model):
    """6.1: Progress reports per term"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress_reports')
    academic_session = models.ForeignKey('curriculum.AcademicSession', on_delete=models.CASCADE, related_name='progress_reports')
    term = models.ForeignKey('curriculum.Term', on_delete=models.CASCADE, related_name='progress_reports')
    school_level = models.ForeignKey('curriculum.SchoolLevel', on_delete=models.CASCADE, related_name='progress_reports')
    total_subjects = models.IntegerField(default=0)
    subjects_passed = models.IntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_grade_point = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    position = models.IntegerField(null=True, blank=True, help_text="Position in class")
    total_students = models.IntegerField(null=True, blank=True)
    teacher_remarks = models.TextField(blank=True)
    principal_remarks = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'progress_reports'
        unique_together = ['student', 'academic_session', 'term']
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.student} - {self.term.name} Report"


class TeacherProfile(models.Model):
    """6.2: Teacher Features - Teacher accounts"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    subjects = models.ManyToManyField('curriculum.Subject', related_name='teachers', blank=True)
    school_levels = models.ManyToManyField('curriculum.SchoolLevel', related_name='teachers', blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    years_of_experience = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teacher_profiles'

    def __str__(self):
        return f"Teacher: {self.user.get_full_name()}"


class TeacherClass(models.Model):
    """6.2: Teacher-Student management - Classes assigned to teachers"""
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='classes')
    school_level = models.ForeignKey('curriculum.SchoolLevel', on_delete=models.CASCADE, related_name='teacher_classes')
    subject = models.ForeignKey('curriculum.Subject', on_delete=models.CASCADE, related_name='teacher_classes')
    academic_session = models.ForeignKey('curriculum.AcademicSession', on_delete=models.CASCADE, related_name='teacher_classes')
    term = models.ForeignKey('curriculum.Term', on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_classes')
    current_week = models.ForeignKey('curriculum.Week', on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_classes')
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_classes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teacher_classes'
        unique_together = ['teacher', 'school_level', 'subject', 'academic_session', 'term']

    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.subject.name} ({self.school_level.name})"


class Assignment(models.Model):
    """6.2: Teacher Features - Assignments"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
    ]
    
    teacher_class = models.ForeignKey(TeacherClass, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    total_marks = models.IntegerField(default=100)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assignments'
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} - {self.teacher_class}"


class AssignmentSubmission(models.Model):
    """Student submissions for assignments"""
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('LATE', 'Late Submission'),
        ('GRADED', 'Graded'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignment_submissions')
    content = models.TextField()
    attachment = models.FileField(upload_to='assignment_submissions/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'assignment_submissions'
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student} - {self.assignment.title}"


class ParentProfile(models.Model):
    """6.3: Parent Portal - Parent accounts"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parent_profile')
    children = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='parents', blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    notification_email = models.BooleanField(default=True)
    notification_sms = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'parent_profiles'

    def __str__(self):
        return f"Parent: {self.user.get_full_name()}"


class Notification(models.Model):
    """6.3: Parent Portal - Notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('GRADE', 'New Grade'),
        ('ASSESSMENT', 'Assessment Due'),
        ('REPORT', 'Progress Report'),
        ('PAYMENT', 'Payment'),
        ('GENERAL', 'General'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user}: {self.title}"


class ContentVersion(models.Model):
    """6.4: Content Management - Version control for syllabuses/content"""
    CONTENT_TYPE_CHOICES = [
        ('CURRICULUM', 'Curriculum'),
        ('TOPIC', 'Topic'),
        ('LESSON', 'Lesson'),
    ]
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.IntegerField()
    version_number = models.IntegerField()
    content_snapshot = models.JSONField(help_text="Snapshot of content at this version")
    change_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='content_versions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content_versions'
        unique_together = ['content_type', 'content_id', 'version_number']
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.content_type} {self.content_id} v{self.version_number}"


class ContentModerationQueue(models.Model):
    """6.4: Content Management - Moderation queue for AI content"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('NEEDS_EDIT', 'Needs Editing'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('LESSON', 'AI-Generated Lesson'),
        ('QUIZ', 'AI-Generated Quiz'),
        ('EXAM', 'AI-Generated Exam'),
    ]
    
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.IntegerField()
    content_preview = models.TextField(help_text="Preview of content for moderation")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_content')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    flagged_issues = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'content_moderation_queue'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.get_content_type_display()} {self.content_id} - {self.get_status_display()}"


class CurriculumUpdateRequest(models.Model):
    """6.4: Content Management - Admin interface for curriculum updates"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('APPLIED', 'Applied'),
    ]
    
    curriculum = models.ForeignKey('curriculum.SubjectCurriculum', on_delete=models.CASCADE, related_name='update_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='curriculum_update_requests')
    change_type = models.CharField(max_length=50, help_text="e.g., 'add_topic', 'update_content', 'reorder'")
    change_description = models.TextField()
    proposed_changes = models.JSONField(help_text="JSON of proposed changes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_curriculum_updates')
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'curriculum_update_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.curriculum} - {self.change_type}"
