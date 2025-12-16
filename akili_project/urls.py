"""
URL configuration for akili_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from core import views as core_views


def health_check(request):
    """Health check endpoint for load balancer and monitoring"""
    return JsonResponse({'status': 'healthy'})


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', core_views.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('dashboard/', core_views.dashboard_view, name='dashboard'),
    
    # App URLs with namespaces
    path('', include('users.urls')),
    path('courses/', include('courses.urls')),
    path('profiles/', include('profiles.urls')),
    path('quizzes/', include('quizzes.urls')),
    path('payments/', include('payments.urls')),
    path('assessments/', include('assessments.urls')),
    
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