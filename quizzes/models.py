# quizzes/models.py

from django.db import models
from django.conf import settings
from courses.models import Module

class QuizAttempt(models.Model):
    """
    Represents a quiz attempt by a user on a specific module.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    module = models.ForeignKey(
        'courses.Module',
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=10)
    questions_data = models.JSONField(default=list)
    completed_at = models.DateTimeField(auto_now_add=True)
    is_retake = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.module.title} ({self.score}/{self.total_questions})"
    
    @property
    def percentage(self):
        return round((self.score / self.total_questions) * 100, 2) if self.total_questions else 0
    
    @property
    def is_passing(self):
        """Check if the score meets the 60% passing threshold"""
        return self.percentage >= 60
