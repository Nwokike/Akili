from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from courses.models import Course
from quizzes.models import QuizAttempt


class HomeViewTestCase(TestCase):
    """Tests for home view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_page_loads(self):
        """Test home page loads for unauthenticated user"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_home_page_content(self):
        """Test home page has expected content"""
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'JS1 to SS3')
    
    def test_home_redirects_authenticated_user(self):
        """Test authenticated user is redirected to dashboard"""
        User = get_user_model()
        user = User.objects.create_user(
            email='home@example.com',
            password='testpass123'
        )
        self.client.login(email='home@example.com', password='testpass123')
        
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))


class DashboardViewTestCase(TestCase):
    """Tests for dashboard view"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='dashboard@example.com',
            password='testpass123'
        )
        cls.user.tutor_credits = 50
        cls.user.save()
    
    def setUp(self):
        self.client = Client()
        self.client.login(email='dashboard@example.com', password='testpass123')
    
    def test_dashboard_loads(self):
        """Test dashboard loads for authenticated user"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_shows_credits(self):
        """Test dashboard shows user credits"""
        response = self.client.get(reverse('dashboard'))
        self.assertIn('user_credits', response.context)
        self.assertEqual(response.context['user_credits'], 50)
    
    def test_dashboard_shows_course_count(self):
        """Test dashboard shows course count"""
        from curriculum.models import SchoolLevel, Term
        
        school_level = SchoolLevel.objects.create(
            name='SS1',
            level_type='SENIOR',
            level_order=4
        )
        term = Term.objects.create(
            name='First Term',
            order=1,
            start_month=9,
            end_month=12,
            instructional_weeks=12
        )
        
        Course.objects.create(
            user=self.user,
            subject='Mathematics',
            school_level=school_level,
            term=term
        )
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['courses_count'], 1)
    
    def test_dashboard_shows_referral_url(self):
        """Test dashboard shows referral URL"""
        response = self.client.get(reverse('dashboard'))
        self.assertIn('referral_url', response.context)


class LegalPagesTestCase(TestCase):
    """Tests for legal pages"""
    
    def setUp(self):
        self.client = Client()
    
    def test_privacy_page_loads(self):
        """Test privacy policy page loads"""
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)
    
    def test_terms_page_loads(self):
        """Test terms of service page loads"""
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)
    
    def test_about_page_loads(self):
        """Test about page loads"""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)


class ErrorPagesTestCase(TestCase):
    """Tests for error pages"""
    
    def setUp(self):
        self.client = Client()
    
    def test_404_page(self):
        """Test 404 page for non-existent URL"""
        response = self.client.get('/nonexistent-page-12345/')
        self.assertEqual(response.status_code, 404)


class ContextProcessorsTestCase(TestCase):
    """Tests for context processors"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='context@example.com',
            password='testpass123'
        )
    
    def setUp(self):
        self.client = Client()
        self.client.login(email='context@example.com', password='testpass123')
    
    def test_dashboard_context_processor(self):
        """Test dashboard context processor adds expected data"""
        response = self.client.get(reverse('dashboard'))
        self.assertIn('user_daily_limit', response.context)
