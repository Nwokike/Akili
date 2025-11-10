from django.contrib import admin
from .models import MockExam


@admin.register(MockExam)
class MockExamAdmin(admin.ModelAdmin):
    list_display = ['user', 'exam_type', 'subject', 'question_count', 'score', 'completed_at']
    list_filter = ['exam_type', 'completed_at']
    search_fields = ['user__username', 'subject']
