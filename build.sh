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

# Seed curriculum data if not already present
# Check if school_levels table has data before seeding
python manage.py shell -c "
from curriculum.models import SchoolLevel
if SchoolLevel.objects.count() == 0:
    print('No curriculum data found. Running seed_curriculum...')
    exit(1)
else:
    print('Curriculum data already exists. Skipping seed.')
    exit(0)
" && echo "Skipping seed_curriculum" || python manage.py seed_curriculum
