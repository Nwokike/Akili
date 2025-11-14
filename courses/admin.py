from django.contrib import admin
# FIX: Removed CachedLesson from import list as it no longer exists in courses.models
from .models import Course, Module 


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


# FIX: The registration block for CachedLesson is REMOVED entirely 
# as the model is no longer in courses/models.py.