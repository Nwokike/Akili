from django.db import models
from django.conf import settings
from courses.models import Module  # adjust import if needed

class Question(models.Model):
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
    score = models.IntegerField()
    questions_data = models.JSONField()

    def __str__(self):
        return f"{self.user} - {self.module} ({self.score})"
