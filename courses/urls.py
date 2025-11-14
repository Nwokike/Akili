from django.urls import path
from . import views

# Define the namespace for this app, required for the reverse() calls in views.py
app_name = 'courses'

urlpatterns = [
    # URL for the main course list/dashboard
    path('', views.CourseDashboardView.as_view(), name='dashboard'),
    
    # URL for creating a new course
    path('new/', views.CourseCreationView.as_view(), name='create_course'), 
]