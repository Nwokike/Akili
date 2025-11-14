from django.shortcuts import render, redirect 
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.db import transaction 
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth import logout as auth_logout # Renamed logout to avoid potential conflict


class ProfileView(LoginRequiredMixin, View):
    """
    Developer 1 Task: Displays the user's profile details and referral information.
    """
    def get(self, request):
        max_referral_credits = settings.AKILI_MAX_REFERRAL_CREDITS 
        
        context = {
            'user_profile': request.user,
            'title': 'My Profile & Settings',
            'max_referral_credits': max_referral_credits,
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

        user = request.user
        
        with transaction.atomic():
            # 1. Log the user out (important!)
            auth_logout(request) # Using the alias
            
            # 2. Delete the user 
            user.delete() 

        messages.success(request, "Your account has been successfully deleted.")
        return redirect(reverse('home'))