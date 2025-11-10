def credits_processor(request):
    """
    Add user credits to template context
    """
    if request.user.is_authenticated:
        request.user.reset_daily_credits()
        return {
            'user_credits': request.user.tutor_credits,
            'user_daily_limit': request.user.daily_credit_limit
        }
    return {}
