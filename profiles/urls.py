from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # Profile page
    path('', views.ProfileView.as_view(), name='my_profile'),
    path('delete/', views.DeleteAccountView.as_view(), name='delete_account'),
]