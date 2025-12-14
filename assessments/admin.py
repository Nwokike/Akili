from django.contrib import admin
from .models import (
    Assessment, AssessmentQuestion, AssessmentSubmission, Grade, ProgressReport,
    TeacherProfile, TeacherClass, Assignment, AssignmentSubmission,
    ParentProfile, Notification,
    ContentVersion, ContentModerationQueue, CurriculumUpdateRequest
)


class AssessmentQuestionInline(admin.TabularInline):
    model = AssessmentQuestion
    extra = 1


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'assessment_type', 'curriculum', 'status', 'due_date', 'created_at']
    list_filter = ['assessment_type', 'status', 'created_at']
    search_fields = ['title', 'curriculum__subject__name']
    inlines = [AssessmentQuestionInline]


@admin.register(AssessmentSubmission)
class AssessmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assessment', 'score', 'status', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['student__email', 'assessment__title']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'curriculum', 'term', 'total_score', 'grade_letter', 'remarks']
    list_filter = ['term', 'grade_letter']
    search_fields = ['student__email', 'curriculum__subject__name']


@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_session', 'term', 'school_level', 'average_score', 'position']
    list_filter = ['academic_session', 'term', 'school_level']
    search_fields = ['student__email']


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'qualification', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__email', 'employee_id']
    filter_horizontal = ['subjects', 'school_levels']


@admin.register(TeacherClass)
class TeacherClassAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'school_level', 'subject', 'term', 'academic_session']
    list_filter = ['academic_session', 'school_level', 'term']
    search_fields = ['teacher__user__email', 'subject__name']
    filter_horizontal = ['students']
    raw_id_fields = ['current_week']


class AssignmentSubmissionInline(admin.TabularInline):
    model = AssignmentSubmission
    extra = 0
    readonly_fields = ['submitted_at']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher_class', 'status', 'due_date', 'total_marks']
    list_filter = ['status', 'due_date']
    search_fields = ['title', 'teacher_class__subject__name']
    inlines = [AssignmentSubmissionInline]


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'notification_email', 'notification_sms']
    search_fields = ['user__email', 'phone_number']
    filter_horizontal = ['children']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title']


@admin.register(ContentVersion)
class ContentVersionAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'content_id', 'version_number', 'created_by', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['change_summary']


@admin.register(ContentModerationQueue)
class ContentModerationQueueAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'content_id', 'status', 'submitted_at', 'reviewed_by']
    list_filter = ['content_type', 'status', 'submitted_at']
    search_fields = ['content_preview']


@admin.register(CurriculumUpdateRequest)
class CurriculumUpdateRequestAdmin(admin.ModelAdmin):
    list_display = ['curriculum', 'change_type', 'status', 'requested_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['curriculum__subject__name', 'change_description']
