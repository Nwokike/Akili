from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from django.conf import settings


class CustomUserModelTestCase(TestCase):
    """Tests for CustomUser model"""
    
    def setUp(self):
        self.User = get_user_model()
    
    def test_create_user_with_email(self):
        """Test creating a regular user with email"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_user_without_email_raises_error(self):
        """Test creating user without email raises ValueError"""
        with self.assertRaises(ValueError):
            self.User.objects.create_user(
                email='',
                password='testpass123'
            )
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin = self.User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
    
    def test_username_auto_generated(self):
        """Test username is auto-generated from email"""
        user = self.User.objects.create_user(
            email='john.doe@example.com',
            password='testpass123'
        )
        self.assertTrue(user.username.startswith('john.doe'))
    
    def test_get_full_name(self):
        """Test get_full_name method"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.get_full_name(), 'John Doe')
    
    def test_default_credits(self):
        """Test user gets default credits"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.tutor_credits, settings.AKILI_DAILY_FREE_CREDITS)
    
    def test_deduct_credits_success(self):
        """Test successful credit deduction"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.tutor_credits = 20
        user.save()
        
        result = user.deduct_credits(5)
        self.assertTrue(result)
        self.assertEqual(user.tutor_credits, 15)
    
    def test_deduct_credits_insufficient(self):
        """Test credit deduction with insufficient credits"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.tutor_credits = 3
        user.save()
        
        result = user.deduct_credits(5)
        self.assertFalse(result)
        self.assertEqual(user.tutor_credits, 3)
    
    def test_add_credits(self):
        """Test adding credits"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        initial = user.tutor_credits
        user.add_credits(50)
        self.assertEqual(user.tutor_credits, initial + 50)
    
    def test_reset_daily_credits_new_day(self):
        """Test daily credit reset on new day"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.tutor_credits = 2
        user.last_daily_reset = date.today() - timedelta(days=1)
        user.save()
        
        user.reset_daily_credits()
        self.assertEqual(user.tutor_credits, user.daily_credit_limit)
    
    def test_reset_preserves_purchased_credits(self):
        """Test reset doesn't reduce purchased credits"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.tutor_credits = 100
        user.last_daily_reset = date.today() - timedelta(days=1)
        user.save()
        
        user.reset_daily_credits()
        self.assertEqual(user.tutor_credits, 100)
    
    def test_increase_daily_limit(self):
        """Test increasing daily limit from referrals"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        initial_limit = user.daily_credit_limit
        user.increase_daily_limit(2)
        self.assertEqual(user.daily_credit_limit, initial_limit + 2)
    
    def test_daily_limit_max_cap(self):
        """Test daily limit doesn't exceed max"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.increase_daily_limit(1000)
        self.assertLessEqual(user.daily_credit_limit, settings.AKILI_MAX_REFERRAL_CREDITS)


class UserAuthViewsTestCase(TestCase):
    """Tests for user authentication views"""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
    
    def test_signup_page_loads(self):
        """Test signup page loads successfully"""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Start Learning Free')
    
    def test_signup_page_no_exam_reference(self):
        """Test signup page uses new branding (no 'exams' reference)"""
        response = self.client.get(reverse('signup'))
        self.assertNotContains(response, 'mastering Nigerian exams')
        self.assertContains(response, 'JS1 to SS3')
    
    def test_login_page_loads(self):
        """Test login page loads successfully"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_signup_creates_user(self):
        """Test signup form creates user"""
        response = self.client.post(reverse('signup'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'agree_to_terms': True
        })
        self.assertTrue(
            self.User.objects.filter(email='newuser@example.com').exists()
        )
    
    def test_login_success(self):
        """Test successful login"""
        self.User.objects.create_user(
            email='logintest@example.com',
            password='testpass123'
        )
        response = self.client.post(reverse('login'), {
            'email': 'logintest@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_logout(self):
        """Test logout functionality"""
        user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class ReferralSystemTestCase(TestCase):
    """Tests for referral system"""
    
    def setUp(self):
        self.User = get_user_model()
        self.referrer = self.User.objects.create_user(
            email='referrer@example.com',
            password='testpass123',
            first_name='Referrer',
            last_name='User'
        )
    
    def test_referral_url_property(self):
        """Test referral URL is generated"""
        self.assertIn(self.referrer.username, self.referrer.referral_url)
    
    def test_referral_signup_page_shows_referrer(self):
        """Test referral signup shows referrer name"""
        client = Client()
        response = client.get(f'/join/{self.referrer.username}')
        if response.status_code == 200:
            self.assertContains(response, self.referrer.first_name)


class PasswordResetTestCase(TestCase):
    """Tests for password reset flow"""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='resetuser@example.com',
            password='testpass123',
            first_name='Reset',
            last_name='User'
        )
    
    def test_password_reset_page_loads(self):
        """Test password reset page loads successfully"""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
    
    def test_password_reset_form_submission(self):
        """Test password reset form accepts valid email"""
        response = self.client.post(reverse('password_reset'), {
            'email': 'resetuser@example.com'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_password_reset_done_page(self):
        """Test password reset done page loads"""
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)


class ProfileViewsTestCase(TestCase):
    """Tests for profile-related views"""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='profileuser@example.com',
            password='testpass123',
            first_name='Profile',
            last_name='User'
        )
        self.client.login(email='profileuser@example.com', password='testpass123')
    
    def test_profile_page_requires_login(self):
        """Test profile page requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('profiles:my_profile'))
        self.assertEqual(response.status_code, 302)
    
    def test_profile_page_loads_when_authenticated(self):
        """Test profile page loads for authenticated user"""
        response = self.client.get(reverse('profiles:my_profile'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_loads_when_authenticated(self):
        """Test dashboard loads for authenticated user"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
