"""
URL configuration for akili_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('', core_views.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('dashboard/', core_views.dashboard_view, name='dashboard'),
    path('exam-center/', core_views.exam_center_view, name='exam_center'),
    
    # App URLs with namespaces
    path('courses/', include('courses.urls')),
    path('profiles/', include('profiles.urls')),
    path('quizzes/', include('quizzes.urls')),
    path('exams/', include('exams.urls')),
    path('payments/', include('payments.urls')),
    
    # Legal pages
    path('privacy/', core_views.privacy_view, name='privacy'),
    path('terms/', core_views.terms_view, name='terms'),
    path('about/', core_views.about_view, name='about'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.error_404_view'
handler500 = 'core.views.error_500_view'
handler403 = 'core.views.error_403_view'