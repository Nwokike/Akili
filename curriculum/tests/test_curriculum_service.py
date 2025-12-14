from django.test import TestCase
from django.contrib.auth import get_user_model
from curriculum.models import (
    AcademicSession, SchoolLevel, Subject, Term, Week,
    SubjectCurriculum, Topic, StudentProgramme, SubjectEnrolment
)
from core.services.curriculum import CurriculumService
from datetime import date


class CurriculumServiceTestCase(TestCase):
    """Unit tests for CurriculumService - Phase 4.5"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        cls.session = AcademicSession.objects.create(
            name='2024/2025',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 7, 31),
            is_active=True
        )
        
        cls.js1 = SchoolLevel.objects.create(
            name='JS1',
            level_order=1,
            level_type='JUNIOR',
            description='Junior Secondary 1'
        )
        
        cls.ss3 = SchoolLevel.objects.create(
            name='SS3',
            level_order=6,
            level_type='SENIOR',
            description='Senior Secondary 3'
        )
        
        cls.math = Subject.objects.create(
            name='Mathematics',
            code='MTH',
            is_science_subject=True
        )
        cls.math.school_levels.add(cls.js1, cls.ss3)
        
        cls.english = Subject.objects.create(
            name='English Language',
            code='ENG',
            is_science_subject=False
        )
        cls.english.school_levels.add(cls.js1, cls.ss3)
        
        cls.first_term = Term.objects.create(
            name='First Term',
            order=1,
            total_weeks=14,
            instructional_weeks=12,
            exam_weeks=2
        )
        
        for i in range(1, 15):
            week_type = 'INSTRUCTIONAL' if i <= 12 else ('REVISION' if i == 13 else 'EXAM')
            Week.objects.create(
                term=cls.first_term,
                week_number=i,
                week_type=week_type,
                title=f'Week {i}'
            )
        
        cls.curriculum = SubjectCurriculum.objects.create(
            school_level=cls.js1,
            subject=cls.math,
            term=cls.first_term,
            version='2025',
            overview='Mathematics curriculum for JS1 First Term'
        )
        
        week1 = Week.objects.get(term=cls.first_term, week_number=1)
        cls.topic = Topic.objects.create(
            curriculum=cls.curriculum,
            week=week1,
            title='Number Systems',
            order=1,
            difficulty_level='BASIC'
        )
    
    def test_get_school_levels(self):
        levels = CurriculumService.get_school_levels()
        self.assertEqual(levels.count(), 2)
        self.assertEqual(levels.first().name, 'JS1')
    
    def test_get_school_level_by_name(self):
        level = CurriculumService.get_school_level_by_name('JS1')
        self.assertIsNotNone(level)
        self.assertEqual(level.level_type, 'JUNIOR')
        
        missing = CurriculumService.get_school_level_by_name('JS99')
        self.assertIsNone(missing)
    
    def test_get_school_level_by_id(self):
        level = CurriculumService.get_school_level_by_id(self.js1.id)
        self.assertIsNotNone(level)
        self.assertEqual(level.name, 'JS1')
    
    def test_get_subjects_for_level(self):
        subjects = CurriculumService.get_subjects_for_level(self.js1)
        self.assertEqual(subjects.count(), 2)
        self.assertIn(self.math, subjects)
    
    def test_get_subjects_for_level_by_id(self):
        subjects = CurriculumService.get_subjects_for_level_by_id(self.js1.id)
        self.assertEqual(subjects.count(), 2)
        
        empty = CurriculumService.get_subjects_for_level_by_id(99999)
        self.assertEqual(empty.count(), 0)
    
    def test_get_terms(self):
        terms = CurriculumService.get_terms()
        self.assertEqual(terms.count(), 1)
        self.assertEqual(terms.first().name, 'First Term')
    
    def test_get_curriculum(self):
        curriculum = CurriculumService.get_curriculum(
            self.js1, self.math, self.first_term
        )
        self.assertIsNotNone(curriculum)
        self.assertEqual(curriculum.version, '2025')
        
        missing = CurriculumService.get_curriculum(
            self.ss3, self.math, self.first_term
        )
        self.assertIsNone(missing)
    
    def test_get_topics_for_curriculum(self):
        topics = CurriculumService.get_topics_for_curriculum(self.curriculum)
        self.assertEqual(topics.count(), 1)
        self.assertEqual(topics.first().title, 'Number Systems')
    
    def test_get_weeks_for_term(self):
        weeks = CurriculumService.get_weeks_for_term(self.first_term)
        self.assertEqual(weeks.count(), 14)
    
    def test_get_active_session(self):
        session = CurriculumService.get_active_session()
        self.assertIsNotNone(session)
        self.assertEqual(session.name, '2024/2025')
    
    def test_get_or_create_programme(self):
        programme = CurriculumService.get_or_create_programme(
            self.user, self.js1, self.session
        )
        self.assertIsNotNone(programme)
        self.assertEqual(programme.school_level, self.js1)
        self.assertTrue(programme.is_active)
        
        same_programme = CurriculumService.get_or_create_programme(
            self.user, self.js1, self.session
        )
        self.assertEqual(programme.id, same_programme.id)
    
    def test_create_enrolment(self):
        enrolment = CurriculumService.create_enrolment(
            self.user, self.js1, self.math, self.first_term, self.session
        )
        self.assertIsNotNone(enrolment)
        self.assertEqual(enrolment.subject, self.math)
        self.assertEqual(enrolment.current_term, self.first_term)
    
    def test_get_user_enrolments(self):
        CurriculumService.create_enrolment(
            self.user, self.js1, self.math, self.first_term, self.session
        )
        enrolments = CurriculumService.get_user_enrolments(self.user)
        self.assertEqual(enrolments.count(), 1)
    
    def test_calculate_progress(self):
        enrolment = CurriculumService.create_enrolment(
            self.user, self.js1, self.math, self.first_term, self.session
        )
        progress = CurriculumService.calculate_progress(enrolment)
        self.assertIsInstance(progress, float)
        self.assertGreaterEqual(progress, 0.0)
        self.assertLessEqual(progress, 100.0)
    
    def test_get_previous_topics(self):
        week2 = Week.objects.get(term=self.first_term, week_number=2)
        Topic.objects.create(
            curriculum=self.curriculum,
            week=week2,
            title='Fractions',
            order=1
        )
        
        week3 = Week.objects.get(term=self.first_term, week_number=3)
        previous = CurriculumService.get_previous_topics(self.curriculum, week3, limit=5)
        self.assertEqual(len(previous), 2)
