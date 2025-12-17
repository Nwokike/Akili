#!/usr/bin/env bash
# build.sh

set -o errexit  # Exit on error

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create cache table
# "|| true" ensures the build doesn't fail if the table already exists
python manage.py createcachetable || true

# One-time superuser creation
# FIXED: Checks by email and passes arguments correctly (email, password, then named args)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='nwokikeonyeka@gmail.com').exists() or User.objects.create_superuser('nwokikeonyeka@gmail.com', 'Maikel1@', username='Maikel', first_name='Onyeka', last_name='Nwokike')" | python manage.py shell
