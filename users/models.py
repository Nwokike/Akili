from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager # <-- NEW IMPORT
import uuid


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    This fixes the createsuperuser TypeError.
    """
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(('The Email must be set'))
        email = self.normalize_email(email)
        
        # Ensure 'username' is set by deriving it from the email if not provided
        if 'username' not in extra_fields:
            email_base = email.split('@')[0]
            extra_fields.setdefault('username', email_base + str(uuid.uuid4())[:8])

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(('Superuser must have is_superuser=True.'))
        
        # The CustomUserManager handles the missing username and calls create_user
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom User model for Akili platform with freemium credit system.
    Email-only authentication with auto-generated username from email.
    """
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    
    # NEW: Link the custom manager to the model
    objects = CustomUserManager() 
    
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
            # Add a short unique identifier to ensure uniqueness
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
        """Generate referral URL for this user - uses dynamic domain from settings"""
        import os
        # Try to get domain from environment or settings
        base_url = os.getenv('REPLIT_DEV_DOMAIN', os.getenv('REPL_SLUG', 'akili.ng'))
        if base_url and not base_url.startswith('http'):
            base_url = f"https://{base_url}"
        return f"{base_url}/join/{self.username}"
    
    def reset_daily_credits(self):
        """
        Add daily free credits if a new day has started.
        FIXED: Uses max(existing, daily_limit) to ensure paid users keep their purchased credits
        while free users still get their daily allowance topped up.
        """
        from datetime import date
        today = date.today()
        
        if self.last_daily_reset < today:
            # FIXED: Use max() to preserve purchased credits while topping up free users
            # If user has more than daily limit (purchased), keep their balance
            # If user has less than daily limit, top up to daily limit
            self.tutor_credits = max(self.tutor_credits, self.daily_credit_limit)
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
            settings.AKILI_MAX_REFERRAL_CREDITS # Assuming this constant is defined in settings
        )
        self.daily_credit_limit = new_limit
        self.save()