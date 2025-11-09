from django.db import models
from django.conf import settings


class MockExam(models.Model):
    """
    Mock exam attempts (5 credits)
    Developer 2: Implement syllabus-grounded exam generation
    """
    EXAM_CHOICES = [
        ('JAMB', 'JAMB'),
        ('SSCE', 'SSCE'),
        ('JSS', 'JSS'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mock_exams')
    exam_type = models.CharField(max_length=10, choices=EXAM_CHOICES)
    subject = models.CharField(max_length=200)
    question_count = models.IntegerField()
    score = models.IntegerField(null=True, blank=True)
    questions_data = models.JSONField()
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mock_exams'
    
    def __str__(self):
        return f"{self.user.username} - {self.exam_type} {self.subject} ({self.question_count}Q)"
