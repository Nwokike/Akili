# quizzes/models.py

from django.db import models
from django.conf import settings

# Link to the Module model (defined in the 'courses' app)
# Using a string reference to avoid circular dependency on app loading

class QuizAttempt(models.Model):
    """
    Quiz attempts with credit logic. This model stores the entire quiz,
    including questions, choices, and user answers within JSONFields.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    
    # Links to the module this quiz covers (using string reference 'courses.Module')
    module = models.ForeignKey(
        'courses.Module', 
        on_delete=models.CASCADE, 
        related_name='quiz_attempts'
    )
    
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0) # ADDED: Required for scoring calculation
    
    # The JSONField stores the questions, choices, and correct answers for this attempt.
    questions_data = models.JSONField() 
    
    # ADDED: Stores the user's selected answers for review/scoring
    user_answers = models.JSONField(default=dict) 
    
    completed_at = models.DateTimeField(null=True, blank=True) # CHANGED: No longer auto_now_add, set by view on submission
    
    created_at = models.DateTimeField(auto_now_add=True) # ADDED: To track when quiz was generated
    
    class Meta:
        db_table = 'quiz_attempts'
        verbose_name_plural = 'Quiz Attempts'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - Quiz {self.module.title} ({self.score}%)"