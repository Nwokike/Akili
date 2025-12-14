from django.utils import timezone


def credits_processor(request):
    """
    Add user credits to template context.
    Only calls reset_daily_credits() if the day has changed.
    """
    if request.user.is_authenticated:
        today = timezone.now().date()
        if request.user.last_daily_reset != today:
            request.user.reset_daily_credits()
        return {
            'user_credits': request.user.tutor_credits,
            'user_daily_limit': request.user.daily_credit_limit
        }
    return {}
