from django.db import models
from django.conf import settings


class Transaction(models.Model):
    """
    Paystack transaction logging
    Developer 2: Implement Paystack integration
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    credits_purchased = models.IntegerField()
    paystack_reference = models.CharField(max_length=200, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'transactions'
    
    def __str__(self):
        return f"{self.user.username} - {self.credits_purchased} credits (₦{self.amount})"


class CreditPurchase(models.Model):
    """
    Credit purchase packages
    Developer 2: Define pricing tiers
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='credit_purchases')
    credits = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='purchases')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'credit_purchases'
    
    def __str__(self):
        return f"{self.user.username} - {self.credits} credits"
