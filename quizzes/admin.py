from django.contrib import admin
from .models import QuizAttempt


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'module', 'score', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['user__username', 'module__title']
