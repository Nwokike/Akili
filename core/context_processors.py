from django.utils import timezone


def credits_processor(request):
    """
    Add user credits and notifications to template context.
    Only calls reset_daily_credits() if the day has changed.
    """
    if request.user.is_authenticated:
        from assessments.models import Notification
        
        today = timezone.now().date()
        if request.user.last_daily_reset != today:
            request.user.reset_daily_credits()
        
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        has_parent_profile = hasattr(request.user, 'parent_profile')
        has_teacher_profile = hasattr(request.user, 'teacher_profile')
        
        return {
            'user_credits': request.user.tutor_credits,
            'user_daily_limit': request.user.daily_credit_limit,
            'unread_notifications': unread_notifications,
            'has_parent_profile': has_parent_profile,
            'has_teacher_profile': has_teacher_profile,
        }
    return {}
