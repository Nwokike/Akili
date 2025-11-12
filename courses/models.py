from django.db import models
from django.conf import settings


class Course(models.Model):
    """
    User's personalized course
    Developer 1: Implement dashboard and course management
    """
    EXAM_CHOICES = [
        ('JAMB', 'JAMB'),
        ('SSCE', 'SSCE'),
        ('JSS', 'JSS'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    exam_type = models.CharField(max_length=10, choices=EXAM_CHOICES)
    subject = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'courses'
        unique_together = ['user', 'exam_type', 'subject']
    
    def __str__(self):
        return f"{self.user.username} - {self.exam_type} {self.subject}"


class Module(models.Model):
    """
    Course modules (15 per course from AI)
    Developer 1: Implement lesson navigation
    """
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
    
    class Meta:
        db_table = 'modules'
        ordering = ['order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.subject} - Module {self.order}: {self.title}"


class CachedLesson(models.Model):
    """
    Cached AI-generated lessons with two-pass validation
    Developer 1: Implement lesson viewing and validation logic
    """
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
