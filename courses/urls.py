from django.urls import path
from . import views

# Define the namespace for this app, required for the reverse() calls in views.py
app_name = 'courses'

urlpatterns = [
    # URL for the main course list/dashboard
    path('', views.CourseDashboardView.as_view(), name='dashboard'),
    
    # URL for creating a new course
    path('new/', views.CourseCreationView.as_view(), name='create_course'),
    
    # URL for module listing (all modules in a course)
    path('<int:course_id>/modules/', views.ModuleListingView.as_view(), name='module_listing'),
    
    # URL for lesson detail view
    path('module/<int:module_id>/lesson/', views.LessonDetailView.as_view(), name='lesson_detail'),
    
    # URL for asking tutor a question
    path('module/<int:module_id>/ask/', views.AskTutorView.as_view(), name='ask_tutor'),
    
    # URL for reporting an error in lesson
    path('module/<int:module_id>/report/', views.ReportErrorView.as_view(), name='report_error'),
    
    # URL for deleting a course
    path('<int:course_id>/delete/', views.DeleteCourseView.as_view(), name='delete_course'),
]