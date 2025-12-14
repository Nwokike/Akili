from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from exams.models import Exam, ExamQuestion
from courses.models import Course


class ExamModelTestCase(TestCase):
    """Tests for Exam model"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='exam@example.com',
            password='testpass123'
        )
        
        cls.course = Course.objects.create(
            user=cls.user,
            subject='Mathematics',
            exam_type='JAMB'
        )
    
    def test_exam_creation(self):
        """Test creating an exam"""
        exam = Exam.objects.create(
            user=self.user,
            course=self.course,
            title='Mathematics Mock Exam',
            total_questions=20
        )
        self.assertEqual(exam.title, 'Mathematics Mock Exam')
        self.assertEqual(exam.total_questions, 20)
        self.assertIsNone(exam.completed_at)
    
    def test_exam_percentage_calculation(self):
        """Test exam percentage property"""
        exam = Exam.objects.create(
            user=self.user,
            course=self.course,
            title='Test Exam',
            score=15,
            total_questions=20
        )
        self.assertEqual(exam.percentage, 75.0)
    
    def test_exam_percentage_zero_questions(self):
        """Test percentage with zero questions"""
        exam = Exam.objects.create(
            user=self.user,
            course=self.course,
            title='Empty Exam',
            score=0,
            total_questions=0
        )
        self.assertEqual(exam.percentage, 0)
    
    def test_exam_string_representation(self):
        """Test exam string representation"""
        exam = Exam.objects.create(
            user=self.user,
            course=self.course,
            title='Sample Exam'
        )
        self.assertIn('Sample Exam', str(exam))
    
    def test_exam_completion(self):
        """Test marking exam as complete"""
        exam = Exam.objects.create(
            user=self.user,
            course=self.course,
            title='Completion Test',
            total_questions=20
        )
        
        exam.score = 18
        exam.completed_at = timezone.now()
        exam.save()
        
        exam.refresh_from_db()
        self.assertIsNotNone(exam.completed_at)
        self.assertEqual(exam.score, 18)


class ExamQuestionModelTestCase(TestCase):
    """Tests for ExamQuestion model"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='examq@example.com',
            password='testpass123'
        )
        
        cls.course = Course.objects.create(
            user=cls.user,
            subject='Physics',
            exam_type='SSCE'
        )
        
        cls.exam = Exam.objects.create(
            user=cls.user,
            course=cls.course,
            title='Physics Mock',
            total_questions=5
        )
    
    def test_exam_question_creation(self):
        """Test creating an exam question"""
        question = ExamQuestion.objects.create(
            exam=self.exam,
            question_text='What is the speed of light?',
            options={'A': '3x10^8 m/s', 'B': '2x10^8 m/s'},
            correct_answer='A'
        )
        self.assertIn('speed of light', question.question_text)
        self.assertEqual(question.correct_answer, 'A')
    
    def test_exam_question_string_representation(self):
        """Test question string representation"""
        question = ExamQuestion.objects.create(
            exam=self.exam,
            question_text='This is a very long question text that should be truncated',
            options={},
            correct_answer='B'
        )
        self.assertTrue(len(str(question)) <= 50)
    
    def test_question_answer_check(self):
        """Test checking if answer is correct"""
        question = ExamQuestion.objects.create(
            exam=self.exam,
            question_text='Test Question',
            options={'A': 'Option A', 'B': 'Option B'},
            correct_answer='A',
            user_answer='A',
            is_correct=True
        )
        self.assertTrue(question.is_correct)
    
    def test_multiple_questions_per_exam(self):
        """Test exam can have multiple questions"""
        for i in range(5):
            ExamQuestion.objects.create(
                exam=self.exam,
                question_text=f'Question {i+1}',
                options={'A': 'Yes', 'B': 'No'},
                correct_answer='A'
            )
        
        self.assertEqual(self.exam.exam_questions.count(), 5)


class ExamViewsTestCase(TestCase):
    """Tests for exam views"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='examview@example.com',
            password='testpass123'
        )
        cls.user.tutor_credits = 50
        cls.user.save()
        
        cls.course = Course.objects.create(
            user=cls.user,
            subject='Biology',
            exam_type='JAMB'
        )
    
    def setUp(self):
        self.client = Client()
        self.client.login(email='examview@example.com', password='testpass123')
    
    def test_exam_center_loads(self):
        """Test exam center page loads"""
        response = self.client.get(reverse('exam_center'))
        self.assertEqual(response.status_code, 200)
    
    def test_exam_center_requires_login(self):
        """Test exam center requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('exam_center'))
        self.assertEqual(response.status_code, 302)
    
    def test_exam_center_shows_courses(self):
        """Test exam center shows user courses"""
        response = self.client.get(reverse('exam_center'))
        self.assertContains(response, 'Biology')


class ExamHistoryTestCase(TestCase):
    """Tests for exam history"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='examhist@example.com',
            password='testpass123'
        )
        
        cls.course = Course.objects.create(
            user=cls.user,
            subject='Chemistry',
            exam_type='NECO'
        )
    
    def test_user_exam_history(self):
        """Test retrieving user's exam history"""
        Exam.objects.create(
            user=self.user,
            course=self.course,
            title='First Exam',
            score=15,
            total_questions=20,
            completed_at=timezone.now()
        )
        Exam.objects.create(
            user=self.user,
            course=self.course,
            title='Second Exam',
            score=18,
            total_questions=20,
            completed_at=timezone.now()
        )
        
        exams = Exam.objects.filter(user=self.user, completed_at__isnull=False)
        self.assertEqual(exams.count(), 2)
