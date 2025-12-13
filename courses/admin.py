from django.contrib import admin
from .models import Course, Module, CachedLesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['user', 'exam_type', 'subject', 'created_at']
    list_filter = ['exam_type', 'created_at']
    search_fields = ['user__username', 'subject']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'order']
    list_filter = ['course__exam_type']
    search_fields = ['title', 'syllabus_topic']


@admin.register(CachedLesson)
class CachedLessonAdmin(admin.ModelAdmin):
    list_display = ['topic', 'syllabus_version', 'is_validated', 'report_count', 'created_at']
    list_filter = ['is_validated', 'syllabus_version']
    search_fields = ['topic', 'content']
    readonly_fields = ['created_at']