# courses/models.py

from django.db import models
from django.conf import settings
import uuid
from users.models import CustomUser 


class Course(models.Model):
    EXAM_CHOICES = [
        ('JAMB', 'JAMB'),
        ('SSCE', 'SSCE'),
        ('JSS', 'JSS'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    exam_type = models.CharField(max_length=10, choices=EXAM_CHOICES, blank=True, null=True, help_text="Legacy field for backwards compatibility")
    subject = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    school_level = models.ForeignKey(
        'curriculum.SchoolLevel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        help_text="New class-level field (JS1-SS3)"
    )
    term = models.ForeignKey(
        'curriculum.Term',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        help_text="Academic term (First/Second/Third)"
    )
    curriculum = models.ForeignKey(
        'curriculum.SubjectCurriculum',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        help_text="Link to structured curriculum"
    )
    
    class Meta:
        db_table = 'courses'
    
    def __str__(self):
        if self.school_level and self.term:
            return f"{self.user.username} - {self.school_level.name} {self.subject} ({self.term.name})"
        return f"{self.user.username} - {self.exam_type or 'N/A'} {self.subject}"
    
    @property
    def display_name(self):
        if self.school_level and self.term:
            return f"{self.school_level.name} {self.subject} - {self.term.name}"
        return f"{self.exam_type} {self.subject}"
    
    @property
    def level_type(self):
        if self.school_level:
            return self.school_level.level_type
        if self.exam_type:
            return 'SENIOR' if self.exam_type in ['JAMB', 'SSCE'] else 'JUNIOR'
        return None


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=300)
    order = models.IntegerField()
    syllabus_topic = models.CharField(max_length=500)
    lesson_content = models.ForeignKey(
        'CachedLesson',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='modules_using_lesson'
    )
    topic = models.ForeignKey(
        'curriculum.Topic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modules',
        help_text="Link to curriculum topic"
    )
    
    class Meta:
        db_table = 'modules'
        ordering = ['order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.subject} - Module {self.order}: {self.title}"


class CachedLesson(models.Model):
    topic = models.CharField(max_length=500)
    content = models.TextField()
    syllabus_version = models.CharField(max_length=50)
    report_count = models.IntegerField(default=0)
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_lessons'
    )
    
    class Meta:
        db_table = 'cached_lessons'
    
    def __str__(self):
        return f"{self.topic} (Validated: {self.is_validated})"
