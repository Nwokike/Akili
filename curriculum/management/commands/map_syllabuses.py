"""
Phase 5.2: Map existing syllabuses to new curriculum structure
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus
from curriculum.models import (
    LegacyExamMapping, SchoolLevel, Subject, Term, SubjectCurriculum, Topic, Week
)


class Command(BaseCommand):
    help = 'Map existing syllabuses to new curriculum topics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be mapped without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("Mapping existing syllabuses to curriculum topics...")
        
        syllabus_models = [
            ('JAMB', JAMBSyllabus, ['SS3']),
            ('SSCE', SSCESyllabus, ['SS2', 'SS3']),
            ('JSS', JSSSyllabus, ['JS1', 'JS2', 'JS3']),
        ]
        
        total_mapped = 0
        
        for exam_type, model, target_levels in syllabus_models:
            syllabuses = model.objects.all()
            self.stdout.write(f"\nProcessing {exam_type} syllabuses ({syllabuses.count()} subjects)...")
            
            for syllabus in syllabuses:
                mapping = LegacyExamMapping.objects.filter(
                    exam_type=exam_type,
                    subject_name__iexact=syllabus.subject
                ).select_related('curriculum').first()
                
                if mapping and mapping.curriculum:
                    existing_topics = mapping.curriculum.topics.count()
                    self.stdout.write(
                        f"  [OK] {syllabus.subject} -> {mapping.curriculum} ({existing_topics} topics)"
                    )
                    total_mapped += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  [SKIP] {syllabus.subject} - no curriculum mapping")
                    )
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Mapping verification complete: {total_mapped} subjects mapped"))
        
        curricula_count = SubjectCurriculum.objects.count()
        topics_count = Topic.objects.count()
        self.stdout.write(f"Total curricula: {curricula_count}")
        self.stdout.write(f"Total topics: {topics_count}")
