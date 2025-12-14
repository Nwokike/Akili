from django.shortcuts import render, redirect 
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.db import transaction 
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth import logout as auth_logout
from users.models import CustomUser


class ProfileView(LoginRequiredMixin, View):
    """Displays the user's profile details and referral information."""
    def get(self, request):
        max_referral_credits = settings.AKILI_MAX_REFERRAL_CREDITS

        # Calculate actual referral stats (filter by exact username, handle null/blank safely)
        username = request.user.username
        if username:
            referral_count = CustomUser.objects.filter(
                referred_by__isnull=False,
                referred_by=username
            ).exclude(referred_by='').count()
        else:
            referral_count = 0
        bonus_credits_earned = referral_count * 2  # 2 credits per referral

        context = {
            'user_profile': request.user,
            'title': 'My Profile & Settings',
            'max_referral_credits': max_referral_credits,
            'referral_count': referral_count,
            'bonus_credits_earned': bonus_credits_earned,
        }

        return render(request, 'profiles/profile.html', context)
    
class DeleteAccountView(LoginRequiredMixin, View):
    """
    Handles the permanent deletion of a user's account and associated data.
    """
    def post(self, request):
        if settings.ACCOUNT_DELETION_DISABLED:
            messages.error(request, "Account deletion is temporarily disabled.")
            return redirect(reverse('profiles:my_profile'))

        if request.POST.get('confirm_delete') != 'true':
            messages.error(request, "You must check the confirmation box to delete your account.")
            return redirect(reverse('profiles:my_profile'))

        # Validate password confirmation
        password = request.POST.get('password', '')
        if not password:
            messages.error(request, "Please enter your password to confirm account deletion.")
            return redirect(reverse('profiles:my_profile'))
        
        if not request.user.check_password(password):
            messages.error(request, "Incorrect password. Account deletion cancelled.")
            return redirect(reverse('profiles:my_profile'))

        user = request.user
        
        with transaction.atomic():
            # 1. Log the user out (important!)
            auth_logout(request) # Using the alias
            
            # 2. Delete the user 
            user.delete() 

        messages.success(request, "Your account has been successfully deleted.")
        return redirect(reverse('home'))