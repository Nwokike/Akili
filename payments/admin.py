from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'reference', 'amount', 'verified', 'created_at']
    list_filter = ['verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'reference']
    readonly_fields = ['reference', 'created_at']
