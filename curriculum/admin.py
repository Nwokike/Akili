from django.contrib import admin
from .models import (
    AcademicSession, SchoolLevel, Subject, Term, Week,
    SubjectCurriculum, Topic, StudentProgramme, SubjectEnrolment,
    LegacyExamMapping
)


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(SchoolLevel)
class SchoolLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'level_order', 'level_type', 'description']
    list_filter = ['level_type']
    ordering = ['level_order']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_science_subject']
    list_filter = ['is_science_subject', 'school_levels']
    search_fields = ['name', 'code']
    filter_horizontal = ['school_levels']


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'total_weeks', 'instructional_weeks', 'exam_weeks']
    ordering = ['order']


@admin.register(Week)
class WeekAdmin(admin.ModelAdmin):
    list_display = ['term', 'week_number', 'week_type', 'title']
    list_filter = ['term', 'week_type']
    ordering = ['term', 'week_number']


@admin.register(SubjectCurriculum)
class SubjectCurriculumAdmin(admin.ModelAdmin):
    list_display = ['subject', 'school_level', 'term', 'version', 'last_updated']
    list_filter = ['school_level', 'subject', 'term']
    search_fields = ['subject__name', 'overview']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'curriculum', 'week', 'order', 'difficulty_level']
    list_filter = ['curriculum__school_level', 'curriculum__subject', 'difficulty_level']
    search_fields = ['title', 'description']
    ordering = ['curriculum', 'week', 'order']


@admin.register(StudentProgramme)
class StudentProgrammeAdmin(admin.ModelAdmin):
    list_display = ['user', 'academic_session', 'school_level', 'is_active', 'created_at']
    list_filter = ['academic_session', 'school_level', 'is_active']
    search_fields = ['user__username', 'user__email']


@admin.register(SubjectEnrolment)
class SubjectEnrolmentAdmin(admin.ModelAdmin):
    list_display = ['programme', 'subject', 'current_term', 'current_week', 'progress_percentage']
    list_filter = ['subject', 'current_term']
    search_fields = ['programme__user__username']


@admin.register(LegacyExamMapping)
class LegacyExamMappingAdmin(admin.ModelAdmin):
    list_display = ['exam_type', 'subject_name', 'school_level', 'subject']
    list_filter = ['exam_type', 'school_level']
    search_fields = ['subject_name', 'notes']
