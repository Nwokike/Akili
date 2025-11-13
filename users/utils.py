from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

def process_referral(new_user: User, referral_username: str):
    """
    Checks if a user signed up via a referral link and updates credits.
    """
    if not referral_username:
        return

    try:
        # 1. Find the referring user (the person whose link was used)
        referrer = User.objects.get(username=referral_username)
    except User.DoesNotExist:
        # Ignore if the referral link is invalid or the referrer was deleted
        return

    # 2. Check the referred_by field on the new user's model
    # Note: Your registration process must ensure new_user.referred_by is set 
    # to the referrer's username upon sign-up.

    # 3. Update the referrer's credit limit
    # The 'increase_daily_limit' method handles the max limit logic
    referrer.increase_daily_limit(settings.AKILI_CREDITS_PER_REFERRAL)
    
    # You might also want to notify the referrer, but that's a later task.
    print(f"--- INFO: Increased credits for referrer {referrer.username}")