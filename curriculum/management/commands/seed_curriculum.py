from django.core.management.base import BaseCommand, CommandError
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
            raise CommandError(f'Error loading initial data: {e}')
        
        try:
            call_command('loaddata', 'subjects.json', verbosity=0)
            self.stdout.write(self.style.SUCCESS('Loaded subjects'))
        except Exception as e:
            raise CommandError(f'Error loading subjects: {e}')
        
        self._assign_subjects_to_levels()
        mapping_count = self._create_legacy_mappings()
        curriculum_count, topic_count = self._create_curricula_and_topics()
        
        self._verify_counts(mapping_count, curriculum_count, topic_count)
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded Nigerian curriculum data!'))
        self.stdout.write('Summary:')
        self.stdout.write('  - 2 Academic Sessions (2024/2025, 2025/2026)')
        self.stdout.write('  - 6 School Levels (JS1, JS2, JS3, SS1, SS2, SS3)')
        self.stdout.write('  - 3 Terms (First, Second, Third)')
        self.stdout.write('  - 40 Weeks (14 per First/Second Term, 12 for Third Term)')
        self.stdout.write('  - 31 Subjects with school level assignments')
        self.stdout.write(f'  - {mapping_count} legacy exam mappings for JAMB/SSCE/JSS compatibility')
        self.stdout.write(f'  - {curriculum_count} SubjectCurriculum entries')
        self.stdout.write(f'  - {topic_count} Topic entries (all weeks covered)')

    def _verify_counts(self, mapping_count, curriculum_count, topic_count):
        from curriculum.models import SubjectCurriculum, Topic, Week
        
        actual_mappings = LegacyExamMapping.objects.count()
        actual_curricula = SubjectCurriculum.objects.count()
        actual_topics = Topic.objects.count()
        
        if actual_mappings < 100:
            raise CommandError(f'Legacy mappings count too low: {actual_mappings} (expected 100+)')
        
        if actual_curricula < 300:
            raise CommandError(f'SubjectCurriculum count too low: {actual_curricula} (expected 300+)')
        
        total_weeks = Week.objects.count()
        if actual_topics < actual_curricula * 10:
            raise CommandError(f'Topic count too low: {actual_topics} (expected at least {actual_curricula * 10})')
        
        self.stdout.write(self.style.SUCCESS(f'Verification passed: {actual_mappings} mappings, {actual_curricula} curricula, {actual_topics} topics'))

    def _assign_subjects_to_levels(self):
        self.stdout.write('Assigning subjects to school levels...')
        
        junior_levels = SchoolLevel.objects.filter(level_type='JUNIOR')
        senior_levels = SchoolLevel.objects.filter(level_type='SENIOR')
        all_levels = SchoolLevel.objects.all()
        
        all_level_subjects = ['ENG', 'MTH', 'CIV', 'AGR', 'CRS', 'IRS', 'YOR', 'IGB', 'HAU']
        junior_only_subjects = ['BSC', 'BTC', 'SST', 'BUS', 'ICT', 'FRE', 'ART', 'HEC', 'PHE']
        senior_only_subjects = ['PHY', 'CHE', 'BIO', 'ECO', 'GOV', 'LIT', 'HIS', 'GEO', 'COM', 'ACC', 'CSC', 'FMT', 'TDR']
        
        for code in all_level_subjects:
            subject = Subject.objects.get(code=code)
            subject.school_levels.set(all_levels)
        
        for code in junior_only_subjects:
            subject = Subject.objects.get(code=code)
            subject.school_levels.set(junior_levels)
        
        for code in senior_only_subjects:
            subject = Subject.objects.get(code=code)
            subject.school_levels.set(senior_levels)
        
        self.stdout.write(self.style.SUCCESS('Subject-level assignments complete'))

    def _create_legacy_mappings(self):
        self.stdout.write('Creating comprehensive legacy exam mappings...')
        
        ss3 = SchoolLevel.objects.get(name='SS3')
        js3 = SchoolLevel.objects.get(name='JS3')
        
        jamb_subjects = [
            ('English', 'ENG'),
            ('English Language', 'ENG'),
            ('Use of English', 'ENG'),
            ('Mathematics', 'MTH'),
            ('General Mathematics', 'MTH'),
            ('Maths', 'MTH'),
            ('Physics', 'PHY'),
            ('Chemistry', 'CHE'),
            ('Biology', 'BIO'),
            ('Economics', 'ECO'),
            ('Government', 'GOV'),
            ('Govt', 'GOV'),
            ('Literature in English', 'LIT'),
            ('Literature', 'LIT'),
            ('Lit-in-English', 'LIT'),
            ('Agricultural Science', 'AGR'),
            ('Agriculture', 'AGR'),
            ('Agric', 'AGR'),
            ('Agric Science', 'AGR'),
            ('Commerce', 'COM'),
            ('Accounting', 'ACC'),
            ('Principles of Accounts', 'ACC'),
            ('Financial Accounting', 'ACC'),
            ('Geography', 'GEO'),
            ('Christian Religious Knowledge', 'CRS'),
            ('CRK', 'CRS'),
            ('Christian Religious Studies', 'CRS'),
            ('CRS', 'CRS'),
            ('Islamic Religious Knowledge', 'IRS'),
            ('IRK', 'IRS'),
            ('Islamic Studies', 'IRS'),
            ('IRS', 'IRS'),
            ('Islamic Religious Studies', 'IRS'),
            ('History', 'HIS'),
            ('Yoruba', 'YOR'),
            ('Igbo', 'IGB'),
            ('Hausa', 'HAU'),
            ('Civic Education', 'CIV'),
            ('Civics', 'CIV'),
            ('Further Mathematics', 'FMT'),
            ('Further Maths', 'FMT'),
            ('Computer Studies', 'CSC'),
            ('Computer Science', 'CSC'),
        ]
        
        ssce_subjects = [
            ('English Language', 'ENG'),
            ('English', 'ENG'),
            ('Oral English', 'ENG'),
            ('Mathematics', 'MTH'),
            ('General Mathematics', 'MTH'),
            ('Maths', 'MTH'),
            ('Core Mathematics', 'MTH'),
            ('Physics', 'PHY'),
            ('Chemistry', 'CHE'),
            ('Biology', 'BIO'),
            ('Economics', 'ECO'),
            ('Government', 'GOV'),
            ('Govt', 'GOV'),
            ('Literature in English', 'LIT'),
            ('Literature', 'LIT'),
            ('Lit-in-English', 'LIT'),
            ('Agricultural Science', 'AGR'),
            ('Agriculture', 'AGR'),
            ('Agric', 'AGR'),
            ('Agric Science', 'AGR'),
            ('Commerce', 'COM'),
            ('Financial Accounting', 'ACC'),
            ('Accounting', 'ACC'),
            ('Principles of Accounts', 'ACC'),
            ('Book Keeping', 'ACC'),
            ('Bookkeeping', 'ACC'),
            ('Geography', 'GEO'),
            ('Civic Education', 'CIV'),
            ('Civics', 'CIV'),
            ('Christian Religious Studies', 'CRS'),
            ('Christian Religious Knowledge', 'CRS'),
            ('CRS', 'CRS'),
            ('CRK', 'CRS'),
            ('Islamic Studies', 'IRS'),
            ('Islamic Religious Studies', 'IRS'),
            ('IRK', 'IRS'),
            ('IRS', 'IRS'),
            ('History', 'HIS'),
            ('Computer Studies', 'CSC'),
            ('Computer Science', 'CSC'),
            ('Data Processing', 'CSC'),
            ('ICT', 'CSC'),
            ('Further Mathematics', 'FMT'),
            ('Additional Mathematics', 'FMT'),
            ('Further Maths', 'FMT'),
            ('Technical Drawing', 'TDR'),
            ('Technical Drawing/Graphics', 'TDR'),
            ('TD', 'TDR'),
            ('Building Construction', 'TDR'),
            ('Yoruba', 'YOR'),
            ('Igbo', 'IGB'),
            ('Hausa', 'HAU'),
            ('Fine Art', 'ART'),
            ('Fine Arts', 'ART'),
            ('Visual Art', 'ART'),
            ('Visual Arts', 'ART'),
        ]
        
        jss_subjects = [
            ('English Language', 'ENG'),
            ('English', 'ENG'),
            ('English Studies', 'ENG'),
            ('Primary English', 'ENG'),
            ('Mathematics', 'MTH'),
            ('Basic Mathematics', 'MTH'),
            ('Maths', 'MTH'),
            ('Basic Science', 'BSC'),
            ('Integrated Science', 'BSC'),
            ('Science', 'BSC'),
            ('General Science', 'BSC'),
            ('Basic Technology', 'BTC'),
            ('Introductory Technology', 'BTC'),
            ('Intro Tech', 'BTC'),
            ('Basic Tech', 'BTC'),
            ('Technology', 'BTC'),
            ('Social Studies', 'SST'),
            ('Social Science', 'SST'),
            ('Civic Education', 'CIV'),
            ('Civics', 'CIV'),
            ('Agricultural Science', 'AGR'),
            ('Agriculture', 'AGR'),
            ('Agric', 'AGR'),
            ('Agric Science', 'AGR'),
            ('Business Studies', 'BUS'),
            ('Business', 'BUS'),
            ('Computer Studies', 'ICT'),
            ('Computer Science', 'ICT'),
            ('ICT', 'ICT'),
            ('Information Technology', 'ICT'),
            ('Computer', 'ICT'),
            ('French', 'FRE'),
            ('French Language', 'FRE'),
            ('Fine Art', 'ART'),
            ('Fine Arts', 'ART'),
            ('Creative Art', 'ART'),
            ('Creative Arts', 'ART'),
            ('Visual Art', 'ART'),
            ('Visual Arts', 'ART'),
            ('Art', 'ART'),
            ('Music', 'ART'),
            ('Home Economics', 'HEC'),
            ('Home Management', 'HEC'),
            ('Home Econs', 'HEC'),
            ('Physical Education', 'PHE'),
            ('Physical & Health Education', 'PHE'),
            ('PHE', 'PHE'),
            ('Physical Health Education', 'PHE'),
            ('Health Education', 'PHE'),
            ('Christian Religious Studies', 'CRS'),
            ('Christian Religious Knowledge', 'CRS'),
            ('CRS', 'CRS'),
            ('CRK', 'CRS'),
            ('Bible Knowledge', 'CRS'),
            ('Islamic Religious Studies', 'IRS'),
            ('Islamic Studies', 'IRS'),
            ('IRK', 'IRS'),
            ('IRS', 'IRS'),
            ('Arabic', 'IRS'),
            ('Yoruba', 'YOR'),
            ('Yoruba Language', 'YOR'),
            ('Igbo', 'IGB'),
            ('Igbo Language', 'IGB'),
            ('Hausa', 'HAU'),
            ('Hausa Language', 'HAU'),
        ]
        
        count = 0
        for subject_name, code in jamb_subjects:
            subject = Subject.objects.get(code=code)
            _, created = LegacyExamMapping.objects.get_or_create(
                exam_type='JAMB',
                subject_name=subject_name,
                defaults={
                    'school_level': ss3,
                    'subject': subject,
                    'notes': 'JAMB UTME subject mapping'
                }
            )
            if created:
                count += 1
        
        for subject_name, code in ssce_subjects:
            subject = Subject.objects.get(code=code)
            _, created = LegacyExamMapping.objects.get_or_create(
                exam_type='SSCE',
                subject_name=subject_name,
                defaults={
                    'school_level': ss3,
                    'subject': subject,
                    'notes': 'WAEC/NECO SSCE subject mapping'
                }
            )
            if created:
                count += 1
        
        for subject_name, code in jss_subjects:
            subject = Subject.objects.get(code=code)
            _, created = LegacyExamMapping.objects.get_or_create(
                exam_type='JSS',
                subject_name=subject_name,
                defaults={
                    'school_level': js3,
                    'subject': subject,
                    'notes': 'Junior Secondary School exam subject mapping'
                }
            )
            if created:
                count += 1
        
        total = LegacyExamMapping.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Created {count} new legacy exam mappings (total: {total})'))
        return total

    def _create_curricula_and_topics(self):
        from curriculum.models import SubjectCurriculum, Topic, Term, Week
        
        self.stdout.write('Generating full curriculum and topic entries...')
        
        terms = Term.objects.all()
        curriculum_count = 0
        topic_count = 0
        
        difficulty_by_week = {
            1: 'BASIC', 2: 'BASIC', 3: 'BASIC', 4: 'BASIC',
            5: 'INTERMEDIATE', 6: 'INTERMEDIATE', 7: 'INTERMEDIATE',
            8: 'INTERMEDIATE', 9: 'ADVANCED', 10: 'ADVANCED',
            11: 'ADVANCED', 12: 'ADVANCED', 13: 'ADVANCED', 14: 'ADVANCED'
        }
        
        week_type_titles = {
            'INSTRUCTIONAL': 'Core Concepts',
            'REVISION': 'Comprehensive Revision',
            'EXAM': 'Terminal Examination Preparation'
        }
        
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
                            'overview': f'{subject.name} curriculum for {level.name} {term.name}. This curriculum covers all key concepts appropriate for {level.get_level_type_display()} students.',
                            'learning_objectives': [
                                f'Master {level.name} level {subject.name} concepts',
                                f'Apply {term.name} learning objectives',
                                f'Develop critical thinking in {subject.name}',
                                f'Prepare for {level.name} assessments',
                                f'Build foundational knowledge for next level'
                            ]
                        }
                    )
                    if created:
                        curriculum_count += 1
                    
                    all_weeks = term.weeks.all()
                    for week in all_weeks:
                        difficulty = difficulty_by_week.get(week.week_number, 'INTERMEDIATE')
                        week_type_title = week_type_titles.get(week.week_type, 'Core Concepts')
                        
                        if week.week_type == 'REVISION':
                            title = f'{subject.name} - {level.name} - {term.name} - Week {week.week_number}: Revision'
                            description = f'Comprehensive revision of all {subject.name} concepts covered in {term.name}. Consolidate learning and prepare for examinations.'
                            learning_objectives = [
                                f'Review all {term.name} concepts',
                                'Identify and address knowledge gaps',
                                'Practice exam-style questions',
                                'Build confidence for terminal examinations'
                            ]
                            key_concepts = [
                                f'{term.name} Key Topics Review',
                                'Exam Techniques',
                                'Time Management Strategies'
                            ]
                            duration = 90
                        elif week.week_type == 'EXAM':
                            title = f'{subject.name} - {level.name} - {term.name} - Week {week.week_number}: Examination'
                            description = f'Terminal examination period for {subject.name}. Focus on exam preparation and performance.'
                            learning_objectives = [
                                'Demonstrate mastery of term concepts',
                                'Apply knowledge under exam conditions',
                                'Show critical thinking and problem-solving'
                            ]
                            key_concepts = [
                                'Examination Readiness',
                                'Answer Presentation',
                                'Self-Assessment'
                            ]
                            duration = 120
                        else:
                            title = f'{subject.name} - {level.name} - {term.name} - Week {week.week_number}'
                            description = f'Core {subject.name} concepts for Week {week.week_number} of {term.name}. Appropriate for {level.name} students.'
                            learning_objectives = [
                                f'Understand Week {week.week_number} key concepts',
                                'Apply concepts through practice exercises',
                                "Connect to previous week's learning"
                            ]
                            key_concepts = [
                                f'{subject.name} Week {week.week_number} Concept 1',
                                f'{subject.name} Week {week.week_number} Concept 2',
                                f'{subject.name} Week {week.week_number} Concept 3'
                            ]
                            duration = 45 if difficulty == 'BASIC' else 60 if difficulty == 'INTERMEDIATE' else 75
                        
                        topic, t_created = Topic.objects.get_or_create(
                            curriculum=curriculum,
                            week=week,
                            defaults={
                                'title': title,
                                'order': 1,
                                'description': description,
                                'learning_objectives': learning_objectives,
                                'key_concepts': key_concepts,
                                'difficulty_level': difficulty,
                                'estimated_duration_minutes': duration
                            }
                        )
                        if t_created:
                            topic_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {curriculum_count} SubjectCurriculum entries'))
        self.stdout.write(self.style.SUCCESS(f'Created {topic_count} Topic entries (all weeks covered)'))
        return curriculum_count, topic_count
