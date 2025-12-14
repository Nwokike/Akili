from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from quizzes.models import QuizAttempt
from courses.models import Course, Module


class QuizAttemptModelTestCase(TestCase):
    """Tests for QuizAttempt model"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='quiz@example.com',
            password='testpass123'
        )
        
        cls.course = Course.objects.create(
            user=cls.user,
            subject='Mathematics',
            exam_type='JAMB'
        )
        
        cls.module = Module.objects.create(
            course=cls.course,
            title='Algebra',
            order=1,
            syllabus_topic='Quadratic Equations'
        )
    
    def test_quiz_attempt_creation(self):
        """Test creating a quiz attempt"""
        attempt = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=7,
            total_questions=10
        )
        self.assertEqual(attempt.score, 7)
        self.assertEqual(attempt.total_questions, 10)
        self.assertFalse(attempt.is_retake)
    
    def test_quiz_percentage_calculation(self):
        """Test percentage property"""
        attempt = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=8,
            total_questions=10
        )
        self.assertEqual(attempt.percentage, 80.0)
    
    def test_quiz_percentage_zero_questions(self):
        """Test percentage with zero questions"""
        attempt = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=0,
            total_questions=0
        )
        self.assertEqual(attempt.percentage, 0)
    
    def test_is_passing_true(self):
        """Test is_passing with passing score"""
        attempt = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=6,
            total_questions=10
        )
        self.assertTrue(attempt.is_passing)
    
    def test_is_passing_false(self):
        """Test is_passing with failing score"""
        attempt = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=5,
            total_questions=10
        )
        self.assertFalse(attempt.is_passing)
    
    def test_quiz_string_representation(self):
        """Test quiz attempt string representation"""
        attempt = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=7,
            total_questions=10
        )
        self.assertIn('Algebra', str(attempt))
        self.assertIn('7/10', str(attempt))
    
    def test_quiz_retake_flag(self):
        """Test retake flag"""
        QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=5,
            total_questions=10,
            completed_at=timezone.now()
        )
        
        retake = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=8,
            total_questions=10,
            is_retake=True
        )
        self.assertTrue(retake.is_retake)
    
    def test_user_answers_json_field(self):
        """Test user_answers JSON field"""
        answers = {'1': 'A', '2': 'B', '3': 'C'}
        attempt = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=3,
            total_questions=3,
            user_answers=answers
        )
        self.assertEqual(attempt.user_answers, answers)
    
    def test_questions_data_json_field(self):
        """Test questions_data JSON field"""
        questions = [
            {'question': 'What is 2+2?', 'options': ['3', '4', '5'], 'answer': '4'}
        ]
        attempt = QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            questions_data=questions
        )
        self.assertEqual(len(attempt.questions_data), 1)


class QuizViewsTestCase(TestCase):
    """Tests for quiz views"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='quizview@example.com',
            password='testpass123'
        )
        cls.user.tutor_credits = 50
        cls.user.save()
        
        cls.course = Course.objects.create(
            user=cls.user,
            subject='Physics',
            exam_type='SSCE'
        )
        
        cls.module = Module.objects.create(
            course=cls.course,
            title='Motion',
            order=1,
            syllabus_topic='Kinematics'
        )
    
    def setUp(self):
        self.client = Client()
        self.client.login(email='quizview@example.com', password='testpass123')
    
    def test_quiz_requires_login(self):
        """Test quiz pages require authentication"""
        self.client.logout()
        response = self.client.get(reverse('quizzes:start_quiz', args=[self.module.id]))
        self.assertEqual(response.status_code, 302)


class QuizHistoryTestCase(TestCase):
    """Tests for quiz history"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='history@example.com',
            password='testpass123'
        )
        
        cls.course = Course.objects.create(
            user=cls.user,
            subject='Chemistry',
            exam_type='JAMB'
        )
        
        cls.module = Module.objects.create(
            course=cls.course,
            title='Organic Chemistry',
            order=1
        )
    
    def test_multiple_attempts_ordering(self):
        """Test quiz attempts are ordered by date"""
        QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=5,
            total_questions=10,
            completed_at=timezone.now()
        )
        QuizAttempt.objects.create(
            user=self.user,
            module=self.module,
            score=8,
            total_questions=10,
            completed_at=timezone.now()
        )
        
        attempts = QuizAttempt.objects.filter(user=self.user)
        self.assertEqual(attempts.count(), 2)
        self.assertEqual(attempts.first().score, 8)
