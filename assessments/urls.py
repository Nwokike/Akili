from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.assessments_list, name='assessments_list'),
    path('<int:pk>/', views.assessment_detail, name='assessment_detail'),
    path('<int:pk>/result/', views.assessment_result, name='assessment_result'),
    
    path('grades/', views.my_grades, name='my_grades'),
    path('report/<int:pk>/', views.progress_report_view, name='progress_report'),
    
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/class/<int:pk>/', views.class_detail, name='class_detail'),
    path('teacher/class/<int:pk>/analytics/', views.class_analytics, name='class_analytics'),
    
    path('parent/', views.parent_dashboard, name='parent_dashboard'),
    path('parent/child/<int:child_id>/', views.child_progress, name='child_progress'),
    path('parent/payments/', views.parent_payments, name='parent_payments'),
    
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_read'),
    
    path('exam/start/<int:course_id>/', views.start_course_exam, name='start_course_exam'),
    path('exam/<int:exam_id>/', views.course_exam_detail, name='course_exam_detail'),
]
