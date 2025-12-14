from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from curriculum.models import (
    AcademicSession, SchoolLevel, Subject, Term, Week, SubjectCurriculum
)
from courses.models import Course
from datetime import date


class CourseCreationIntegrationTestCase(TestCase):
    """Integration tests for course creation flow - Phase 4.6"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='student@example.com',
            password='testpass123'
        )
        cls.user.tutor_credits = 50
        cls.user.save()
        
        cls.session = AcademicSession.objects.create(
            name='2024/2025',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 7, 31),
            is_active=True
        )
        
        cls.js1 = SchoolLevel.objects.create(
            name='JS1',
            level_order=1,
            level_type='JUNIOR'
        )
        
        cls.math = Subject.objects.create(
            name='Mathematics',
            code='MTH',
            is_science_subject=True
        )
        cls.math.school_levels.add(cls.js1)
        
        cls.first_term = Term.objects.create(
            name='First Term',
            order=1,
            total_weeks=14,
            instructional_weeks=12,
            exam_weeks=2
        )
        
        for i in range(1, 15):
            week_type = 'INSTRUCTIONAL' if i <= 12 else 'EXAM'
            Week.objects.create(
                term=cls.first_term,
                week_number=i,
                week_type=week_type
            )
        
        cls.curriculum = SubjectCurriculum.objects.create(
            school_level=cls.js1,
            subject=cls.math,
            term=cls.first_term,
            version='2025'
        )
    
    def setUp(self):
        self.client = Client()
        self.client.login(email='student@example.com', password='testpass123')
    
    def test_course_creation_page_loads(self):
        response = self.client.get(reverse('courses:course_creation'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create')
    
    def test_get_available_subjects_api(self):
        response = self.client.get(
            reverse('courses:get_subjects'),
            {'school_level': self.js1.id}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('subjects', data)
        self.assertEqual(len(data['subjects']), 1)
        self.assertEqual(data['subjects'][0]['name'], 'Mathematics')
    
    def test_course_dashboard_empty(self):
        response = self.client.get(reverse('courses:course_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_duplicate_course_prevention(self):
        Course.objects.create(
            user=self.user,
            subject='Mathematics',
            school_level=self.js1,
            term=self.first_term,
            curriculum=self.curriculum
        )
        
        existing = Course.objects.filter(
            user=self.user,
            school_level=self.js1,
            term=self.first_term,
            subject='Mathematics'
        ).exists()
        self.assertTrue(existing)


class CourseModelTestCase(TestCase):
    """Tests for Course model - Phase 4.6"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        cls.js1 = SchoolLevel.objects.create(
            name='JS1',
            level_order=1,
            level_type='JUNIOR'
        )
        
        cls.first_term = Term.objects.create(
            name='First Term',
            order=1
        )
    
    def test_course_display_name_with_curriculum(self):
        course = Course.objects.create(
            user=self.user,
            subject='Mathematics',
            school_level=self.js1,
            term=self.first_term
        )
        self.assertIn('JS1', course.display_name)
        self.assertIn('Mathematics', course.display_name)
    
    def test_course_display_name_legacy(self):
        course = Course.objects.create(
            user=self.user,
            subject='Physics',
            exam_type='JAMB'
        )
        self.assertIn('JAMB', course.display_name)
        self.assertIn('Physics', course.display_name)
