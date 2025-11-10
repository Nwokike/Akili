from django.contrib import admin
from .models import JAMBSyllabus, SSCESyllabus, JSSSyllabus


@admin.register(JAMBSyllabus)
class JAMBSyllabusAdmin(admin.ModelAdmin):
    list_display = ['subject', 'version', 'last_updated']
    search_fields = ['subject']
    readonly_fields = ['last_updated']


@admin.register(SSCESyllabus)
class SSCESyllabusAdmin(admin.ModelAdmin):
    list_display = ['subject', 'version', 'last_updated']
    search_fields = ['subject']
    readonly_fields = ['last_updated']


@admin.register(JSSSyllabus)
class JSSSyllabusAdmin(admin.ModelAdmin):
    list_display = ['subject', 'version', 'last_updated']
    search_fields = ['subject']
    readonly_fields = ['last_updated']
