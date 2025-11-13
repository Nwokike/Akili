from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings # Needed for max referral credits, etc.

class ProfileView(LoginRequiredMixin, View):
    """
    Developer 1 Task: Displays the user's profile details and referral information.
    """
    def get(self, request):
        # The user object (request.user) automatically contains all necessary fields
        # (first_name, last_name, email, tutor_credits, etc.)
        
        # We can calculate the maximum possible referral credits for display
        max_referral_credits = settings.AKILI_MAX_REFERRAL_CREDITS # Assuming this setting exists
        
        context = {
            'user_profile': request.user,
            'title': 'My Profile & Settings',
            'max_referral_credits': max_referral_credits,
        }
        
        return render(request, 'profiles/profile.html', context)
    
from django.db import transaction 
from django.contrib import messages
from django.shortcuts import render, redirect 
# ... other imports ...

class DeleteAccountView(LoginRequiredMixin, View):
    """
    Handles the permanent deletion of a user's account and associated data.
    """
    def post(self, request):
        if settings.ACCOUNT_DELETION_DISABLED:
            # You should define this setting in settings.py for safety
            messages.error(request, "Account deletion is temporarily disabled.")
            return redirect(reverse('profiles:my_profile'))

        # Standard check to ensure the user confirms the action
        if request.POST.get('confirm_delete') != 'true':
            messages.error(request, "You must check the confirmation box to delete your account.")
            return redirect(reverse('profiles:my_profile'))

        user = request.user
        
        # Use a transaction to ensure all database operations succeed or fail together
        with transaction.atomic():
            # 1. Log the user out (important!)
            logout(request) 
            
            # 2. Delete the user (Django handles deleting related ForeignKey data via CASCADE)
            user.delete() 

        # Redirect the user to the home page or a confirmation page
        messages.success(request, "Your account has been successfully deleted.")
        return redirect(reverse('home')) # Redirect to the main homepage URL
