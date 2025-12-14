"""
Phase 5.1: Migration script for existing user courses to new curriculum structure
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from courses.models import Course
from curriculum.models import LegacyExamMapping, SchoolLevel, Term
from core.services.curriculum import CurriculumService


class Command(BaseCommand):
    help = 'Migrate existing courses from legacy exam_type to new curriculum structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        legacy_courses = Course.objects.filter(
            exam_type__isnull=False,
            school_level__isnull=True
        ).select_related('user')
        
        total = legacy_courses.count()
        migrated = 0
        failed = 0
        
        self.stdout.write(f"Found {total} legacy courses to migrate")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        default_term = Term.objects.filter(order=1).first()
        if not default_term:
            self.stdout.write(self.style.ERROR("No terms found. Run seed_curriculum first."))
            return
        
        for course in legacy_courses:
            try:
                mapping = LegacyExamMapping.objects.filter(
                    exam_type=course.exam_type,
                    subject_name__iexact=course.subject
                ).select_related('school_level', 'subject', 'curriculum').first()
                
                if not mapping:
                    mapping = LegacyExamMapping.objects.filter(
                        exam_type=course.exam_type,
                        subject_name__icontains=course.subject.split()[0]
                    ).select_related('school_level', 'subject', 'curriculum').first()
                
                if mapping:
                    if not dry_run:
                        with transaction.atomic():
                            course.school_level = mapping.school_level
                            course.term = default_term
                            course.curriculum = mapping.curriculum
                            course.save()
                    
                    self.stdout.write(
                        f"  {'[DRY]' if dry_run else '[OK]'} {course.exam_type} {course.subject} -> "
                        f"{mapping.school_level.name} {mapping.subject.name}"
                    )
                    migrated += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  [SKIP] No mapping for {course.exam_type} {course.subject}")
                    )
                    failed += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  [ERROR] {course.exam_type} {course.subject}: {str(e)}")
                )
                failed += 1
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Migration complete: {migrated} migrated, {failed} failed/skipped"))
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Run without --dry-run to apply changes"))
