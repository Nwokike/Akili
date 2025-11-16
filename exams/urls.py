from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('start/<int:module_id>/', views.start_exam, name='start_exam'),
    path('take/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('results/<int:exam_id>/', views.results, name='results'),
]
