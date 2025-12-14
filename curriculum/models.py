from django.db import models
from django.conf import settings


class AcademicSession(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="e.g., 2024/2025")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'academic_sessions'
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class SchoolLevel(models.Model):
    LEVEL_TYPE_CHOICES = [
        ('JUNIOR', 'Junior Secondary'),
        ('SENIOR', 'Senior Secondary'),
    ]

    name = models.CharField(max_length=10, unique=True, help_text="JS1, JS2, JS3, SS1, SS2, SS3")
    level_order = models.IntegerField(unique=True, help_text="1-6 for ordering")
    level_type = models.CharField(max_length=10, choices=LEVEL_TYPE_CHOICES)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'school_levels'
        ordering = ['level_order']

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True, help_text="e.g., ENG, MTH, PHY")
    school_levels = models.ManyToManyField(SchoolLevel, related_name='subjects')
    is_science_subject = models.BooleanField(default=False, help_text="For LaTeX/formula handling")
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['name']

    def __str__(self):
        return self.name


class Term(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="First Term, Second Term, Third Term")
    order = models.IntegerField(unique=True, help_text="1, 2, or 3")
    total_weeks = models.IntegerField(default=14)
    instructional_weeks = models.IntegerField(default=12)
    exam_weeks = models.IntegerField(default=2)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'terms'
        ordering = ['order']

    def __str__(self):
        return self.name


class Week(models.Model):
    WEEK_TYPE_CHOICES = [
        ('INSTRUCTIONAL', 'Instructional'),
        ('REVISION', 'Revision'),
        ('EXAM', 'Examination'),
    ]

    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.IntegerField(help_text="1-14")
    week_type = models.CharField(max_length=15, choices=WEEK_TYPE_CHOICES, default='INSTRUCTIONAL')
    title = models.CharField(max_length=100, blank=True, help_text="e.g., Week 1: Introduction")
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'weeks'
        ordering = ['term', 'week_number']
        unique_together = ['term', 'week_number']

    def __str__(self):
        return f"{self.term.name} - Week {self.week_number}"


class SubjectCurriculum(models.Model):
    school_level = models.ForeignKey(SchoolLevel, on_delete=models.CASCADE, related_name='curricula')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='curricula')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='curricula')
    version = models.CharField(max_length=50, default="2025")
    overview = models.TextField(blank=True, help_text="Text description of curriculum")
    learning_objectives = models.JSONField(default=list, blank=True, help_text="JSON array of objectives")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subject_curricula'
        unique_together = ['school_level', 'subject', 'term', 'version']

    def __str__(self):
        return f"{self.subject.name} - {self.school_level.name} - {self.term.name}"


class Topic(models.Model):
    DIFFICULTY_CHOICES = [
        ('BASIC', 'Basic'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
    ]

    curriculum = models.ForeignKey(SubjectCurriculum, on_delete=models.CASCADE, related_name='topics')
    week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=300)
    order = models.IntegerField(default=1, help_text="Order within the week")
    description = models.TextField(blank=True)
    learning_objectives = models.JSONField(default=list, blank=True)
    key_concepts = models.JSONField(default=list, blank=True, help_text="JSON array of key concepts")
    difficulty_level = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='BASIC')
    estimated_duration_minutes = models.IntegerField(default=45)

    class Meta:
        db_table = 'topics'
        ordering = ['curriculum', 'week', 'order']

    def __str__(self):
        return f"{self.curriculum.subject.name} Week {self.week.week_number}: {self.title}"


class StudentProgramme(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='programmes')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='student_programmes')
    school_level = models.ForeignKey(SchoolLevel, on_delete=models.CASCADE, related_name='student_programmes')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'student_programmes'
        unique_together = ['user', 'academic_session', 'school_level']

    def __str__(self):
        return f"{self.user.username} - {self.school_level.name} ({self.academic_session.name})"


class SubjectEnrolment(models.Model):
    programme = models.ForeignKey(StudentProgramme, on_delete=models.CASCADE, related_name='enrolments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrolments')
    current_term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrolments')
    current_week = models.ForeignKey(Week, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrolments')
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subject_enrolments'
        unique_together = ['programme', 'subject']

    def __str__(self):
        return f"{self.programme.user.username} - {self.subject.name}"


class LegacyExamMapping(models.Model):
    EXAM_TYPE_CHOICES = [
        ('JAMB', 'JAMB'),
        ('SSCE', 'SSCE'),
        ('JSS', 'JSS'),
    ]

    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES)
    subject_name = models.CharField(max_length=200, help_text="Original subject name from old system")
    school_level = models.ForeignKey(SchoolLevel, on_delete=models.CASCADE, related_name='legacy_mappings')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='legacy_mappings')
    curriculum = models.ForeignKey(SubjectCurriculum, on_delete=models.SET_NULL, null=True, blank=True, related_name='legacy_mappings')
    notes = models.TextField(blank=True, help_text="Additional mapping notes")

    class Meta:
        db_table = 'legacy_exam_mappings'
        unique_together = ['exam_type', 'subject_name']

    def __str__(self):
        return f"{self.exam_type} {self.subject_name} -> {self.subject.name} ({self.school_level.name})"
