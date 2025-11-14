from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction # ADDED FOR TRANSACTION SAFETY
from django.urls import reverse # ADDED FOR REVERSE LOOKUP
from .models import CustomUser
from .forms import SignupForm, LoginForm


def signup_view(request):
    """Handle user signup with optional referral"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    referred_by = request.GET.get('ref', '')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Handle referral
            if referred_by:
                try:
                    # NOTE: This assumes CustomUser.increase_daily_limit is defined.
                    referrer = CustomUser.objects.get(username=referred_by)
                    user.referred_by = referrer.username
                    referrer.increase_daily_limit(2) 
                    user.save()
                except CustomUser.DoesNotExist:
                    pass
            
            login(request, user)
            messages.success(request, 'Welcome to Akili!')
            return redirect('dashboard')
    else:
        form = SignupForm()
    
    return render(request, 'users/signup.html', {
        'form': form,
        'referred_by': referred_by
    })


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


# NOTE: This dashboard is usually in core/views.py, but we keep it here for now
@login_required
def dashboard_view(request):
    """Main dashboard"""
    return render(request, 'core/dashboard.html', {
        'referral_url': f"{request.scheme}://{request.get_host()}/join/{request.user.username}"
    })


def referral_signup_view(request, username):
    """Handle referral signup via /join/username"""
    return redirect(f'{reverse("signup")}?ref={username}')

# --- FINAL ACCOUNT DELETION LOGIC ---
@login_required
def delete_account_view(request):
    """Handle permanent account deletion via POST request."""
    if request.method == 'POST':
        
        # Use transaction for atomic deletion
        with transaction.atomic():
            user = request.user
            # We store the username to show a message *after* logout
            username = user.username
            
            # 1. Log the user out first to invalidate their session
            logout(request)
            
            # 2. Now, delete the user object (CASCADE handles related data)
            user.delete()
        
        messages.success(request, f"Account '{username}' has been permanently deleted.")
        return redirect('signup') # Redirect to the public signup page
    else:
        # If accessed via GET (e.g., typing the URL), send them to the profile page
        messages.error(request, "Invalid request. Use the profile page to delete.")
        # NOTE: Using profiles:my_profile ensures the new URL works
        return redirect(reverse('profiles:my_profile'))