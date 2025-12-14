"""
Phase 5.2: Map existing syllabuses to new curriculum structure
Creates LegacyExamMapping entries and populates SubjectCurriculum/Topic from legacy syllabuses
"""
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus
from curriculum.models import (
    LegacyExamMapping, SchoolLevel, Subject, Term, SubjectCurriculum, Topic, Week
)


class Command(BaseCommand):
    help = 'Map existing syllabuses to new curriculum topics and create curriculum entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be mapped without making changes',
        )

    def extract_topics_from_syllabus(self, syllabus_content):
        """Parse syllabus markdown content to extract topic titles."""
        topics = []
        lines = syllabus_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('## ') or line.startswith('### '):
                topic_title = line.lstrip('#').strip()
                if topic_title and len(topic_title) > 3:
                    topic_title = re.sub(r'^\d+[\.\)]\s*', '', topic_title)
                    if topic_title:
                        topics.append(topic_title)
            elif line.startswith('- ') or line.startswith('* '):
                item = line.lstrip('-* ').strip()
                if len(item) > 10 and ':' in item[:50]:
                    topic_title = item.split(':')[0].strip()
                    if topic_title and len(topic_title) > 3:
                        topics.append(topic_title)
        
        if len(topics) < 5:
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    item = line.lstrip('-* ').strip()
                    if len(item) > 5 and item not in topics:
                        topics.append(item[:200])
        
        return topics

    def get_or_create_subject(self, subject_name):
        """Find matching Subject or return None."""
        subject_name_lower = subject_name.lower().strip()
        
        name_mappings = {
            'english language': 'English Language',
            'english': 'English Language',
            'mathematics': 'Mathematics',
            'maths': 'Mathematics',
            'physics': 'Physics',
            'chemistry': 'Chemistry',
            'biology': 'Biology',
            'economics': 'Economics',
            'government': 'Government',
            'literature in english': 'Literature in English',
            'literature': 'Literature in English',
            'geography': 'Geography',
            'agricultural science': 'Agricultural Science',
            'agriculture': 'Agricultural Science',
            'commerce': 'Commerce',
            'accounting': 'Financial Accounting',
            'financial accounting': 'Financial Accounting',
            'computer science': 'Computer Science',
            'computer studies': 'Computer Science',
            'ict': 'Computer Science',
            'further mathematics': 'Further Mathematics',
            'civic education': 'Civic Education',
            'civics': 'Civic Education',
            'history': 'History',
            'christian religious studies': 'Christian Religious Studies',
            'crs': 'Christian Religious Studies',
            'islamic religious studies': 'Islamic Religious Studies',
            'irs': 'Islamic Religious Studies',
            'basic science': 'Basic Science',
            'basic technology': 'Basic Technology',
            'social studies': 'Social Studies',
            'business studies': 'Business Studies',
            'home economics': 'Home Economics',
            'fine art': 'Fine Art',
            'physical education': 'Physical and Health Education',
            'yoruba': 'Yoruba',
            'igbo': 'Igbo',
            'hausa': 'Hausa',
            'french': 'French',
            'technical drawing': 'Technical Drawing',
        }
        
        mapped_name = name_mappings.get(subject_name_lower)
        if mapped_name:
            subject = Subject.objects.filter(name=mapped_name).first()
            if subject:
                return subject
        
        subject = Subject.objects.filter(name__iexact=subject_name).first()
        if subject:
            return subject
        
        for word in subject_name_lower.split():
            if len(word) > 3:
                subject = Subject.objects.filter(name__icontains=word).first()
                if subject:
                    return subject
        
        return None

    def get_difficulty_for_week(self, week_number):
        """Determine difficulty level based on week number."""
        if week_number <= 4:
            return 'BASIC'
        elif week_number <= 10:
            return 'INTERMEDIATE'
        else:
            return 'ADVANCED'

    def distribute_topics(self, topics, num_slots):
        """Distribute topics evenly across slots, handling remainders."""
        if not topics:
            return [[] for _ in range(num_slots)]
        
        result = [[] for _ in range(num_slots)]
        for i, topic in enumerate(topics):
            result[i % num_slots].append(topic)
        return result

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("Mapping existing syllabuses to curriculum structure...")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
        
        syllabus_configs = [
            ('JAMB', JAMBSyllabus, ['SS3']),
            ('SSCE', SSCESyllabus, ['SS2', 'SS3']),
            ('JSS', JSSSyllabus, ['JS1', 'JS2', 'JS3']),
        ]
        
        terms = list(Term.objects.all().order_by('order'))
        if not terms:
            self.stdout.write(self.style.ERROR("No terms found. Run seed_curriculum first."))
            return
        
        stats = {
            'mappings_created': 0,
            'mappings_updated': 0,
            'curricula_created': 0,
            'topics_created': 0,
            'skipped': 0,
        }
        
        for exam_type, model, target_levels in syllabus_configs:
            syllabuses = model.objects.all()
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Processing {exam_type} syllabuses ({syllabuses.count()} subjects)...")
            self.stdout.write('='*60)
            
            for syllabus in syllabuses:
                subject = self.get_or_create_subject(syllabus.subject)
                
                if not subject:
                    self.stdout.write(
                        self.style.WARNING(f"  [SKIP] {syllabus.subject} - no matching subject found")
                    )
                    stats['skipped'] += 1
                    continue
                
                topics_extracted = self.extract_topics_from_syllabus(syllabus.syllabus_content)
                
                existing_mapping = LegacyExamMapping.objects.filter(
                    exam_type=exam_type,
                    subject_name=syllabus.subject
                ).first()
                
                primary_level = SchoolLevel.objects.filter(name=target_levels[0]).first()
                if not primary_level:
                    continue
                
                first_curriculum = None
                
                for level_name in target_levels:
                    school_level = SchoolLevel.objects.filter(name=level_name).first()
                    if not school_level:
                        continue
                    
                    if not dry_run:
                        topics_per_term = self.distribute_topics(topics_extracted, len(terms))
                        
                        for term_idx, term in enumerate(terms):
                            curriculum, curr_created = SubjectCurriculum.objects.get_or_create(
                                school_level=school_level,
                                subject=subject,
                                term=term,
                                defaults={
                                    'version': syllabus.version,
                                    'overview': f"Curriculum for {subject.name} at {school_level.name} level, {term.name}",
                                    'learning_objectives': [],
                                }
                            )
                            
                            if curr_created:
                                stats['curricula_created'] += 1
                            
                            if first_curriculum is None and level_name == target_levels[0] and term.order == 1:
                                first_curriculum = curriculum
                            
                            weeks = Week.objects.filter(
                                term=term,
                                week_type='INSTRUCTIONAL'
                            ).order_by('week_number')
                            
                            term_topics = topics_per_term[term_idx] if term_idx < len(topics_per_term) else []
                            
                            weeks_list = list(weeks)
                            for topic_idx, topic_title in enumerate(term_topics):
                                week_idx = topic_idx % len(weeks_list) if weeks_list else 0
                                week = weeks_list[week_idx] if weeks_list else None
                                if not week:
                                    continue
                                
                                order = (topic_idx // len(weeks_list)) + 1
                                
                                existing = Topic.objects.filter(
                                    curriculum=curriculum,
                                    week=week,
                                    title=topic_title[:300]
                                ).exists()
                                
                                if not existing:
                                    Topic.objects.create(
                                        curriculum=curriculum,
                                        week=week,
                                        title=topic_title[:300],
                                        order=order,
                                        description=f"Topic from {exam_type} syllabus for {subject.name}",
                                        learning_objectives=[],
                                        key_concepts=[],
                                        difficulty_level=self.get_difficulty_for_week(week.week_number),
                                        estimated_duration_minutes=45,
                                    )
                                    stats['topics_created'] += 1
                
                if not dry_run:
                    if existing_mapping:
                        if existing_mapping.curriculum is None and first_curriculum:
                            existing_mapping.curriculum = first_curriculum
                            existing_mapping.notes = f"Updated from {exam_type} syllabus v{syllabus.version}"
                            existing_mapping.save()
                            stats['mappings_updated'] += 1
                            self.stdout.write(
                                f"  [UPDATED] {syllabus.subject} -> {subject.name} - curriculum linked"
                            )
                        else:
                            self.stdout.write(
                                f"  [EXISTS] {syllabus.subject} -> {existing_mapping.subject.name}"
                            )
                    else:
                        LegacyExamMapping.objects.create(
                            exam_type=exam_type,
                            subject_name=syllabus.subject,
                            school_level=primary_level,
                            subject=subject,
                            curriculum=first_curriculum,
                            notes=f"Auto-mapped from {exam_type} syllabus v{syllabus.version}"
                        )
                        stats['mappings_created'] += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  [CREATED] {syllabus.subject} -> {subject.name} - "
                                f"{len(topics_extracted)} topics extracted"
                            )
                        )
                elif dry_run:
                    self.stdout.write(
                        f"  [WOULD {'UPDATE' if existing_mapping else 'CREATE'}] "
                        f"{syllabus.subject} -> {subject.name} - {len(topics_extracted)} topics"
                    )
        
        self.stdout.write("")
        self.stdout.write("="*60)
        self.stdout.write(self.style.SUCCESS("Mapping Complete!"))
        self.stdout.write("="*60)
        self.stdout.write(f"Legacy mappings created: {stats['mappings_created']}")
        self.stdout.write(f"Legacy mappings updated: {stats['mappings_updated']}")
        self.stdout.write(f"Curricula created: {stats['curricula_created']}")
        self.stdout.write(f"Topics created: {stats['topics_created']}")
        self.stdout.write(f"Subjects skipped (no match): {stats['skipped']}")
        self.stdout.write("")
        self.stdout.write(f"Total LegacyExamMappings: {LegacyExamMapping.objects.count()}")
        self.stdout.write(f"Total SubjectCurricula: {SubjectCurriculum.objects.count()}")
        self.stdout.write(f"Total Topics: {Topic.objects.count()}")
