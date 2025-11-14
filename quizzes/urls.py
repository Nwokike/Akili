# quizzes/urls.py

from django.urls import path
from . import views # This line requires views.py to exist

app_name = 'quizzes'

urlpatterns = [
    path('start/<int:module_id>/', views.start_quiz_view, name='start_quiz'),
    path('<int:quiz_id>/', views.quiz_detail_view, name='quiz_detail'),
    path('history/', views.quiz_history_view, name='quiz_history'),
]