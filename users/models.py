from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid


class CustomUser(AbstractUser):
    """
    Custom User model for Akili platform with freemium credit system.
    Email-only authentication with auto-generated username from email.
    """
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    # Freemium Credit System Fields
    tutor_credits = models.IntegerField(default=settings.AKILI_DAILY_FREE_CREDITS)
    last_daily_reset = models.DateField(auto_now_add=True)
    daily_credit_limit = models.IntegerField(default=settings.AKILI_DAILY_FREE_CREDITS)
    
    # Referral System
    referred_by = models.CharField(max_length=150, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def save(self, *args, **kwargs):
        """Auto-generate username from email (just the part before @)"""
        if not self.username:
            email_base = self.email.split('@')[0]
            self.username = email_base + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'akili_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.get_full_name() or self.email
    
    def get_full_name(self):
        """Return the user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def referral_url(self):
        """Generate referral URL for this user"""
        return f"akili.ng/join/{self.username}"
    
    def reset_daily_credits(self):
        """Reset daily credits if needed"""
        from datetime import date
        today = date.today()
        
        if self.last_daily_reset < today:
            self.tutor_credits = self.daily_credit_limit
            self.last_daily_reset = today
            self.save()
    
    def deduct_credits(self, amount):
        """Deduct credits and return True if successful"""
        self.reset_daily_credits()
        
        if self.tutor_credits >= amount:
            self.tutor_credits -= amount
            self.save()
            return True
        return False
    
    def add_credits(self, amount):
        """Add purchased credits (don't reset)"""
        self.tutor_credits += amount
        self.save()
    
    def increase_daily_limit(self, amount):
        """Increase daily credit limit (from referrals)"""
        new_limit = min(
            self.daily_credit_limit + amount,
            settings.AKILI_MAX_REFERRAL_CREDITS
        )
        self.daily_credit_limit = new_limit
        self.save()
