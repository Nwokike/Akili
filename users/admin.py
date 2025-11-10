from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'tutor_credits', 'daily_credit_limit', 'referred_by', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Akili Credits & Referrals', {
            'fields': ('tutor_credits', 'daily_credit_limit', 'last_daily_reset', 'referred_by')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Akili Credits & Referrals', {
            'fields': ('tutor_credits', 'daily_credit_limit', 'referred_by')
        }),
    )
