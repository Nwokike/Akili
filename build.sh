#!/usr/bin/env bash
# build.sh

set -o errexit  # Exit on error

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# One-time superuser creation
# This checks if the new user exists and creates it if not.
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='onyeka.nwokike.245742@unn.edu.ng').exists() or User.objects.create_superuser('onyeka.nwokike.245742@unn.edu.ng', 'Maikel1@')" | python manage.py shell
