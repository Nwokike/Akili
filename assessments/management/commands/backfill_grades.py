"""
Management command to backfill grades from existing quiz attempts.
"""
from django.core.management.base import BaseCommand
from assessments.services import backfill_all_grades


class Command(BaseCommand):
    help = 'Backfill grades from existing completed quiz attempts'

    def handle(self, *args, **options):
        self.stdout.write('Starting grade backfill...')
        
        total_grades, total_users = backfill_all_grades()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully backfilled {total_grades} grades for {total_users} users'
            )
        )
