#!/usr/bin/env bash
# build.sh

set -o errexit  # Exit on error

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# One-time superuser creation (remove this line after your first successful deploy)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); email='nwokikeonyeka@gmail.com'; User.objects.filter(email=email).exists() or User.objects.create_superuser(email=email, password='Onyeka1@', first_name='Onyeka', last_name='Nwokike')" | python manage.py shell
