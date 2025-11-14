# courses/models.py

from django.db import models
from django.conf import settings
import uuid
from users.models import CustomUser 
# Assuming CustomUser and CustomUserManager definitions are present in users/models.py

class Course(models.Model):
    """
    User's personalized course. Subject and Exam Type are stored here.
    """
    EXAM_CHOICES = [
        ('JAMB', 'JAMB'),
        ('SSCE', 'SSCE'),
        ('JSS', 'JSS'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    exam_type = models.CharField(max_length=10, choices=EXAM_CHOICES)
    subject = models.CharField(max_length=200) # Subject field is here
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'courses'
        unique_together = ['user', 'exam_type', 'subject']
    
    def __str__(self):
        return f"{self.user.username} - {self.exam_type} {self.subject}"


class Module(models.Model):
    """
    Course modules (linked to the Course parent).
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules') # Links to parent Course
    title = models.CharField(max_length=300)
    order = models.IntegerField()
    syllabus_topic = models.CharField(max_length=500)
    
    # FIX: REMOVE THE FOREIGN KEY TO CACHEDLESSON, as that model no longer exists
    # lesson_content = models.ForeignKey(
    #     'CachedLesson',
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     blank=True,
    #     related_name='modules_using_lesson'
    # )
    
    class Meta:
        db_table = 'modules'
        ordering = ['order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        # FIX: Access subject via parent course
        return f"{self.course.subject} - Module {self.order}: {self.title}"

# If CachedLesson was defined here, remove it now.