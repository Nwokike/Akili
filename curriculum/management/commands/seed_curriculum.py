from django.core.management.base import BaseCommand
from django.core.management import call_command
from curriculum.models import Subject, SchoolLevel, LegacyExamMapping


class Command(BaseCommand):
    help = 'Seeds the curriculum database with Nigerian academic structure data'

    def handle(self, *args, **options):
        self.stdout.write('Loading initial curriculum data...')
        
        try:
            call_command('loaddata', 'initial_data.json', verbosity=0)
            self.stdout.write(self.style.SUCCESS('Loaded academic sessions, school levels, terms, and weeks'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading initial data: {e}'))
            return
        
        try:
            call_command('loaddata', 'subjects.json', verbosity=0)
            self.stdout.write(self.style.SUCCESS('Loaded subjects'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading subjects: {e}'))
            return
        
        self._assign_subjects_to_levels()
        self._create_legacy_mappings()
        self._load_sample_curricula()
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded Nigerian curriculum data!'))
        self.stdout.write('Summary:')
        self.stdout.write('  - 2 Academic Sessions (2024/2025, 2025/2026)')
        self.stdout.write('  - 6 School Levels (JS1, JS2, JS3, SS1, SS2, SS3)')
        self.stdout.write('  - 3 Terms (First, Second, Third)')
        self.stdout.write('  - 40 Weeks (14 per First/Second Term, 12 for Third Term)')
        self.stdout.write('  - 31 Subjects with school level assignments')
        self.stdout.write('  - Legacy exam mappings for JAMB/SSCE/JSS compatibility')

    def _assign_subjects_to_levels(self):
        self.stdout.write('Assigning subjects to school levels...')
        
        junior_levels = SchoolLevel.objects.filter(level_type='JUNIOR')
        senior_levels = SchoolLevel.objects.filter(level_type='SENIOR')
        all_levels = SchoolLevel.objects.all()
        
        all_level_subjects = ['ENG', 'MTH', 'CIV', 'AGR', 'CRS', 'IRS', 'YOR', 'IGB', 'HAU']
        junior_only_subjects = ['BSC', 'BTC', 'SST', 'BUS', 'ICT', 'FRE', 'ART', 'HEC', 'PHE']
        senior_only_subjects = ['PHY', 'CHE', 'BIO', 'ECO', 'GOV', 'LIT', 'HIS', 'GEO', 'COM', 'ACC', 'CSC', 'FMT', 'TDR']
        
        for code in all_level_subjects:
            try:
                subject = Subject.objects.get(code=code)
                subject.school_levels.set(all_levels)
            except Subject.DoesNotExist:
                pass
        
        for code in junior_only_subjects:
            try:
                subject = Subject.objects.get(code=code)
                subject.school_levels.set(junior_levels)
            except Subject.DoesNotExist:
                pass
        
        for code in senior_only_subjects:
            try:
                subject = Subject.objects.get(code=code)
                subject.school_levels.set(senior_levels)
            except Subject.DoesNotExist:
                pass
        
        self.stdout.write(self.style.SUCCESS('Subject-level assignments complete'))

    def _create_legacy_mappings(self):
        self.stdout.write('Creating legacy exam mappings...')
        
        ss3 = SchoolLevel.objects.get(name='SS3')
        js3 = SchoolLevel.objects.get(name='JS3')
        
        jamb_subjects = [
            ('English', 'ENG'),
            ('Mathematics', 'MTH'),
            ('Physics', 'PHY'),
            ('Chemistry', 'CHE'),
            ('Biology', 'BIO'),
            ('Economics', 'ECO'),
            ('Government', 'GOV'),
            ('Literature in English', 'LIT'),
            ('Agricultural Science', 'AGR'),
            ('Commerce', 'COM'),
            ('Accounting', 'ACC'),
            ('Geography', 'GEO'),
            ('Christian Religious Knowledge', 'CRS'),
            ('Islamic Religious Knowledge', 'IRS'),
            ('History', 'HIS'),
            ('Yoruba', 'YOR'),
            ('Igbo', 'IGB'),
            ('Hausa', 'HAU'),
        ]
        
        for subject_name, code in jamb_subjects:
            try:
                subject = Subject.objects.get(code=code)
                LegacyExamMapping.objects.get_or_create(
                    exam_type='JAMB',
                    subject_name=subject_name,
                    defaults={
                        'school_level': ss3,
                        'subject': subject,
                        'notes': 'JAMB UTME subject mapping'
                    }
                )
            except Subject.DoesNotExist:
                pass
        
        ssce_subjects = [
            ('English Language', 'ENG'),
            ('Mathematics', 'MTH'),
            ('Physics', 'PHY'),
            ('Chemistry', 'CHE'),
            ('Biology', 'BIO'),
            ('Economics', 'ECO'),
            ('Government', 'GOV'),
            ('Literature in English', 'LIT'),
            ('Agricultural Science', 'AGR'),
            ('Commerce', 'COM'),
            ('Financial Accounting', 'ACC'),
            ('Geography', 'GEO'),
            ('Civic Education', 'CIV'),
            ('Christian Religious Studies', 'CRS'),
            ('Islamic Studies', 'IRS'),
            ('History', 'HIS'),
            ('Computer Studies', 'CSC'),
            ('Further Mathematics', 'FMT'),
            ('Technical Drawing', 'TDR'),
            ('Yoruba', 'YOR'),
            ('Igbo', 'IGB'),
            ('Hausa', 'HAU'),
        ]
        
        for subject_name, code in ssce_subjects:
            try:
                subject = Subject.objects.get(code=code)
                LegacyExamMapping.objects.get_or_create(
                    exam_type='SSCE',
                    subject_name=subject_name,
                    defaults={
                        'school_level': ss3,
                        'subject': subject,
                        'notes': 'WAEC/NECO SSCE subject mapping'
                    }
                )
            except Subject.DoesNotExist:
                pass
        
        jss_subjects = [
            ('English Language', 'ENG'),
            ('Mathematics', 'MTH'),
            ('Basic Science', 'BSC'),
            ('Basic Technology', 'BTC'),
            ('Social Studies', 'SST'),
            ('Civic Education', 'CIV'),
            ('Agricultural Science', 'AGR'),
            ('Business Studies', 'BUS'),
            ('Computer Studies', 'ICT'),
            ('French', 'FRE'),
            ('Fine Art', 'ART'),
            ('Home Economics', 'HEC'),
            ('Physical Education', 'PHE'),
            ('Christian Religious Studies', 'CRS'),
            ('Islamic Religious Studies', 'IRS'),
            ('Yoruba', 'YOR'),
            ('Igbo', 'IGB'),
            ('Hausa', 'HAU'),
        ]
        
        for subject_name, code in jss_subjects:
            try:
                subject = Subject.objects.get(code=code)
                LegacyExamMapping.objects.get_or_create(
                    exam_type='JSS',
                    subject_name=subject_name,
                    defaults={
                        'school_level': js3,
                        'subject': subject,
                        'notes': 'Junior Secondary School exam subject mapping'
                    }
                )
            except Subject.DoesNotExist:
                pass
        
        count = LegacyExamMapping.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Created {count} legacy exam mappings'))

    def _load_sample_curricula(self):
        from curriculum.models import SubjectCurriculum, Topic, Term, Week
        
        self.stdout.write('Generating SubjectCurriculum entries for all levels...')
        
        terms = Term.objects.all()
        curriculum_count = 0
        topic_count = 0
        
        for level in SchoolLevel.objects.all():
            subjects = level.subjects.all()
            for subject in subjects:
                for term in terms:
                    curriculum, created = SubjectCurriculum.objects.get_or_create(
                        school_level=level,
                        subject=subject,
                        term=term,
                        version='2025',
                        defaults={
                            'overview': f'{subject.name} curriculum for {level.name} {term.name}',
                            'learning_objectives': [
                                f'Master {level.name} level {subject.name} concepts',
                                f'Apply {term.name} learning objectives',
                                f'Prepare for {level.name} assessments'
                            ]
                        }
                    )
                    if created:
                        curriculum_count += 1
                        
                        weeks = term.weeks.filter(week_type='INSTRUCTIONAL')[:3]
                        for i, week in enumerate(weeks, 1):
                            Topic.objects.get_or_create(
                                curriculum=curriculum,
                                week=week,
                                defaults={
                                    'title': f'{subject.name} {level.name} {term.name} Week {week.week_number} Topic',
                                    'order': 1,
                                    'description': f'Core concepts for Week {week.week_number}',
                                    'learning_objectives': [f'Objective {i}' for i in range(1, 4)],
                                    'key_concepts': [f'Concept {i}' for i in range(1, 4)],
                                    'difficulty_level': 'BASIC' if i == 1 else 'INTERMEDIATE',
                                    'estimated_duration_minutes': 45
                                }
                            )
                            topic_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {curriculum_count} SubjectCurriculum entries'))
        self.stdout.write(self.style.SUCCESS(f'Created {topic_count} Topic entries'))
