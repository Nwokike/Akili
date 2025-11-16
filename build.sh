#!/usr/bin/env bash
# build.sh

set -o errexit  # Exit on error

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# One-time superuser creation/update
# This will find the user and make them a superuser,
# or create them as a superuser if they don't exist.
echo "from django.contrib.auth import get_user_model; User = get_user_model(); email = 'nwokikeonyeka@gmail.com'; password = 'Maikel1@'; try: user = User.objects.get(email=email); updated = False; if not user.is_superuser: user.is_superuser = True; updated = True; if not user.is_staff: user.is_staff = True; updated = True; if updated: user.save(); print(f'Updated {email} to superuser.'); else: print(f'{email} is already a superuser.'); except User.DoesNotExist: User.objects.create_superuser(email, password); print(f'Created superuser {email}.')" | python manage.py shell
