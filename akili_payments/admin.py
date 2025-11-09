from django.contrib import admin
from .models import Transaction, CreditPurchase


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'credits_purchased', 'status', 'paystack_reference', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'paystack_reference']
    readonly_fields = ['paystack_reference', 'created_at']


@admin.register(CreditPurchase)
class CreditPurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'credits', 'amount', 'transaction', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
