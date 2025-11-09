"""
URL configuration for akili_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from akili_core import views as core_views

urlpatterns = [
    path('', lambda request: redirect('login' if not request.user.is_authenticated else 'dashboard'), name='home'),
    path('admin/', admin.site.urls),
    path('', include('akili_users.urls')),
    path('dashboard/', core_views.dashboard_view, name='dashboard'),
    path('exam-center/', core_views.exam_center_view, name='exam_center'),
    path('profile/', core_views.profile_view, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
