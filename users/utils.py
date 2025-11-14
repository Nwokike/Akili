from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth Views
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Referral Handling (e.g., /join/username)
    path('join/<str:username>/', views.referral_signup_view, name='referral_signup'),
    
    # Dashboard (if dashboard is kept in the users app)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # --- PROFILES / ACCOUNT DELETION PATH ---
    path('delete-account/', views.delete_account_view, name='delete_account'),
    
    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]