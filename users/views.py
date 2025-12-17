from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout as auth_logout
from django.conf import settings
from .models import CustomUser
from .forms import SignupForm, LoginForm


@ensure_csrf_cookie
def signup_view(request):
    """Handle user signup with optional referral"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    referred_by = request.GET.get('ref', '')
    referrer_name = ''

    # Get referrer's friendly name for display
    if referred_by:
        try:
            referrer = CustomUser.objects.get(username=referred_by)
            referrer_name = referrer.first_name or referrer.get_full_name() or referred_by
        except CustomUser.DoesNotExist:
            referred_by = ''  # Invalid referrer

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Use commit=False to set referral before saving
            user = form.save(commit=False)

            # Handle referral
            if referred_by:
                try:
                    referrer = CustomUser.objects.get(username=referred_by)
                    user.referred_by = referrer.username
                except CustomUser.DoesNotExist:
                    pass

            # Save user and any M2M relationships
            user.save()
            form.save_m2m()

            # Award referral bonus after user is saved
            if referred_by and user.referred_by:
                try:
                    referrer = CustomUser.objects.get(username=referred_by)
                    referrer.increase_daily_limit(2)
                except CustomUser.DoesNotExist:
                    pass

            login(request, user)
            messages.success(request, 'Welcome to Akili!')
            return redirect('dashboard')
    else:
        form = SignupForm()

    return render(request, 'users/signup.html', {
        'form': form,
        'referred_by': referred_by,
        'referrer_name': referrer_name
    })


@ensure_csrf_cookie
def login_view(request):
    """Handle user login with email"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Note: authenticate uses USERNAME_FIELD, which is email in CustomUser
            user = authenticate(request, username=email, password=password) 
            
            if user is not None:
                login(request, user)
                messages.success(request, 'Welcome back!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def referral_signup_view(request, username):
    """Handle referral signup via /join/username"""
    return redirect(f'{reverse("signup")}?ref={username}')


class ProfileView(LoginRequiredMixin, View):
    """Displays the user's profile details and referral information."""
    def get(self, request):
        max_referral_credits = settings.AKILI_MAX_REFERRAL_CREDITS

        username = request.user.username
        if username:
            referral_count = CustomUser.objects.filter(
                referred_by__isnull=False,
                referred_by=username
            ).exclude(referred_by='').count()
        else:
            referral_count = 0
        bonus_credits_earned = referral_count * settings.AKILI_CREDITS_PER_REFERRAL

        context = {
            'user_profile': request.user,
            'title': 'My Profile & Settings',
            'max_referral_credits': max_referral_credits,
            'referral_count': referral_count,
            'bonus_credits_earned': bonus_credits_earned,
        }

        return render(request, 'profiles/profile.html', context)


class DeleteAccountView(LoginRequiredMixin, View):
    """Handles the permanent deletion of a user's account and associated data."""
    def post(self, request):
        if getattr(settings, 'ACCOUNT_DELETION_DISABLED', False):
            messages.error(request, "Account deletion is temporarily disabled.")
            return redirect(reverse('profiles:my_profile'))

        if request.POST.get('confirm_delete') != 'true':
            messages.error(request, "You must check the confirmation box to delete your account.")
            return redirect(reverse('profiles:my_profile'))

        password = request.POST.get('password', '')
        if not password:
            messages.error(request, "Please enter your password to confirm account deletion.")
            return redirect(reverse('profiles:my_profile'))
        
        if not request.user.check_password(password):
            messages.error(request, "Incorrect password. Account deletion cancelled.")
            return redirect(reverse('profiles:my_profile'))

        user = request.user
        
        with transaction.atomic():
            auth_logout(request)
            user.delete()

        messages.success(request, "Your account has been successfully deleted.")
        return redirect(reverse('home'))

