from django.db import models
from django.conf import settings


class QuizAttempt(models.Model):
    """
    Quiz attempts with credit logic
    Developer 2: Implement quiz generation and scoring
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    module = models.ForeignKey('akili_courses.Module', on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.IntegerField()
    questions_data = models.JSONField()
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quiz_attempts'
    
    def __str__(self):
        return f"{self.user.username} - Quiz {self.module.title} ({self.score}%)"
