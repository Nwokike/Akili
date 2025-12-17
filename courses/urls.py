from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseDashboardView.as_view(), name='course_list'),
    
    path('new/', views.CourseCreationView.as_view(), name='create_course'),
    
    path('tutor/', views.TutorHubView.as_view(), name='tutor_hub'),
    
    path('api/subjects/', views.GetAvailableSubjectsView.as_view(), name='get_subjects'),
    
    path('<int:course_id>/modules/', views.ModuleListingView.as_view(), name='module_listing'),
    
    path('module/<int:module_id>/lesson/', views.LessonDetailView.as_view(), name='lesson_detail'),
    
    path('module/<int:module_id>/ask/', views.AskTutorView.as_view(), name='ask_tutor'),
    
    path('module/<int:module_id>/report/', views.ReportErrorView.as_view(), name='report_error'),
    
    path('<int:course_id>/delete/', views.DeleteCourseView.as_view(), name='delete_course'),
]
