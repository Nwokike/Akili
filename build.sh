#!/usr/bin/env bash
# build.sh

set -o errexit  # Exit on error

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# One-time superuser creation (run once, then remove or secure)
# This checks if the user 'Maikel' exists and creates it if not.
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='Maikel').exists() or User.objects.create_superuser('Maikel', 'nwokikeonyeka@gmail.com', 'Maikel1@')" | python manage.py shell