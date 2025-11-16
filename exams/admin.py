from django.contrib import admin
from .models import Exam, ExamQuestion


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'score', 'total_questions', 'percentage', 'started_at', 'completed_at']
    list_filter = ['started_at', 'completed_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['started_at']


@admin.register(ExamQuestion)
class ExamQuestionAdmin(admin.ModelAdmin):
    list_display = ['exam', 'question_text', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['question_text', 'exam__title']
