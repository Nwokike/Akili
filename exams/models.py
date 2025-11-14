from django.db import models
from django.conf import settings


class Exam(models.Model):
    """
    Represents a full mock exam attempt by a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exam_attempts"
    )
    module = models.ForeignKey(
        "courses.Module",
        on_delete=models.CASCADE,
        related_name="exam_attempts"
    )
    title = models.CharField(max_length=255)
    score = models.IntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.title}"

    @property
    def percentage(self):
        return round((self.score / self.total_questions) * 100, 2) if self.total_questions else 0


class ExamQuestion(models.Model):
    """
    Questions shown to a user during a mock exam.
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="exam_questions"
    )
    question_text = models.TextField()
    options = models.JSONField(default=dict)
    correct_answer = models.CharField(max_length=255)
    user_answer = models.CharField(max_length=255, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.question_text[:50]
