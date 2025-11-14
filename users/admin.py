from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'get_full_name', 'username', 'tutor_credits', 'daily_credit_limit', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    # Custom fieldsets excluding the non-editable username field
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Akili Credits & Referrals', {
            'fields': ('tutor_credits', 'daily_credit_limit', 'last_daily_reset', 'referred_by')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
        ('Akili Credits & Referrals', {
            'fields': ('tutor_credits', 'daily_credit_limit', 'referred_by')
        }),
    )
    
    readonly_fields = ['username', 'last_login', 'date_joined']
