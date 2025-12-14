from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
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
        response = self.client.get(reverse('courses:create_course'))
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
        response = self.client.get(reverse('courses:course_list'))
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


class CourseCreationPOSTTestCase(TestCase):
    """POST workflow tests for course creation - Phase 4.6 FIX"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='posttest@example.com',
            password='testpass123'
        )
        cls.user.tutor_credits = 50
        cls.user.save()
        
        cls.poor_user = cls.User.objects.create_user(
            email='poor@example.com',
            password='testpass123'
        )
        cls.poor_user.tutor_credits = 2
        cls.poor_user.save()
        
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
        
        cls.english = Subject.objects.create(
            name='English Language',
            code='ENG',
            is_science_subject=False
        )
        cls.english.school_levels.add(cls.js1)
        
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
        
        cls.math_curriculum = SubjectCurriculum.objects.create(
            school_level=cls.js1,
            subject=cls.math,
            term=cls.first_term,
            version='2025'
        )
        
        cls.eng_curriculum = SubjectCurriculum.objects.create(
            school_level=cls.js1,
            subject=cls.english,
            term=cls.first_term,
            version='2025'
        )
    
    def setUp(self):
        self.client = Client()
    
    @patch('courses.views.generate_course_modules')
    def test_post_course_creation_success(self, mock_generate):
        """Test successful course creation via POST deducts credits"""
        mock_generate.return_value = True
        self.client.login(email='posttest@example.com', password='testpass123')
        
        initial_credits = self.user.tutor_credits
        
        response = self.client.post(
            reverse('courses:create_course'),
            {
                'school_level': str(self.js1.id),
                'term': str(self.first_term.id),
                'subject': str(self.math.id),
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.tutor_credits, initial_credits - 5)
        
        course_exists = Course.objects.filter(
            user=self.user,
            school_level=self.js1,
            term=self.first_term,
            subject='Mathematics'
        ).exists()
        self.assertTrue(course_exists)
        
        mock_generate.assert_called_once()
    
    @patch('courses.views.generate_course_modules')
    def test_post_duplicate_course_prevention(self, mock_generate):
        """Test POST prevents duplicate course creation"""
        mock_generate.return_value = True
        self.client.login(email='posttest@example.com', password='testpass123')
        
        Course.objects.create(
            user=self.user,
            subject='English Language',
            school_level=self.js1,
            term=self.first_term,
            curriculum=self.eng_curriculum
        )
        
        initial_credits = self.user.tutor_credits
        
        response = self.client.post(
            reverse('courses:create_course'),
            {
                'school_level': str(self.js1.id),
                'term': str(self.first_term.id),
                'subject': str(self.english.id),
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.tutor_credits, initial_credits)
        
        mock_generate.assert_not_called()
    
    def test_post_insufficient_credits(self):
        """Test POST fails gracefully with insufficient credits"""
        self.client.login(email='poor@example.com', password='testpass123')
        
        initial_credits = self.poor_user.tutor_credits
        
        response = self.client.post(
            reverse('courses:create_course'),
            {
                'school_level': str(self.js1.id),
                'term': str(self.first_term.id),
                'subject': str(self.math.id),
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'credits')
        
        self.poor_user.refresh_from_db()
        self.assertEqual(self.poor_user.tutor_credits, initial_credits)
        
        course_exists = Course.objects.filter(
            user=self.poor_user,
            school_level=self.js1,
            term=self.first_term,
            subject='Mathematics'
        ).exists()
        self.assertFalse(course_exists)
    
    @patch('courses.views.generate_course_modules')
    def test_post_curriculum_linkage(self, mock_generate):
        """Test course is properly linked to curriculum"""
        mock_generate.return_value = True
        self.client.login(email='posttest@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('courses:create_course'),
            {
                'school_level': str(self.js1.id),
                'term': str(self.first_term.id),
                'subject': str(self.math.id),
            }
        )
        
        course = Course.objects.get(
            user=self.user,
            school_level=self.js1,
            term=self.first_term,
            subject='Mathematics'
        )
        
        self.assertEqual(course.curriculum, self.math_curriculum)
        self.assertEqual(course.school_level, self.js1)
        self.assertEqual(course.term, self.first_term)
