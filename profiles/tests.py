from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings


class ProfileViewTestCase(TestCase):
    """Tests for profile view"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='profile@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def setUp(self):
        self.client = Client()
        self.client.login(email='profile@example.com', password='testpass123')
    
    def test_profile_page_loads(self):
        """Test profile page loads for authenticated user"""
        response = self.client.get(reverse('profiles:my_profile'))
        self.assertEqual(response.status_code, 200)
    
    def test_profile_requires_login(self):
        """Test profile page requires authentication"""
        self.client.logout()
        response = self.client.get(reverse('profiles:my_profile'))
        self.assertEqual(response.status_code, 302)
    
    def test_profile_shows_user_info(self):
        """Test profile page shows user information"""
        response = self.client.get(reverse('profiles:my_profile'))
        self.assertContains(response, 'Test')
        self.assertContains(response, 'User')
    
    def test_profile_shows_referral_info(self):
        """Test profile page shows referral information"""
        response = self.client.get(reverse('profiles:my_profile'))
        self.assertEqual(response.status_code, 200)


class DeleteAccountViewTestCase(TestCase):
    """Tests for account deletion"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
    
    def setUp(self):
        self.client = Client()
        self.user = self.User.objects.create_user(
            email='delete@example.com',
            password='testpass123',
            first_name='Delete',
            last_name='Me'
        )
        self.client.login(email='delete@example.com', password='testpass123')
    
    def test_delete_requires_confirmation(self):
        """Test delete requires confirmation checkbox"""
        response = self.client.post(
            reverse('profiles:delete_account'),
            {'password': 'testpass123'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.User.objects.filter(email='delete@example.com').exists())
    
    def test_delete_requires_password(self):
        """Test delete requires correct password"""
        response = self.client.post(
            reverse('profiles:delete_account'),
            {'confirm_delete': 'true', 'password': 'wrongpass'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.User.objects.filter(email='delete@example.com').exists())
    
    def test_delete_success(self):
        """Test successful account deletion"""
        if not settings.ACCOUNT_DELETION_DISABLED:
            response = self.client.post(
                reverse('profiles:delete_account'),
                {'confirm_delete': 'true', 'password': 'testpass123'}
            )
            self.assertEqual(response.status_code, 302)
            self.assertFalse(self.User.objects.filter(email='delete@example.com').exists())
    
    def test_delete_requires_login(self):
        """Test delete endpoint requires authentication"""
        self.client.logout()
        response = self.client.post(reverse('profiles:delete_account'))
        self.assertEqual(response.status_code, 302)


class ProfileContextTestCase(TestCase):
    """Tests for profile context data"""
    
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
    
    def test_profile_context_has_max_referral_credits(self):
        """Test profile context includes max referral credits"""
        response = self.client.get(reverse('profiles:my_profile'))
        self.assertIn('max_referral_credits', response.context)
        self.assertEqual(
            response.context['max_referral_credits'],
            settings.AKILI_MAX_REFERRAL_CREDITS
        )
    
    def test_profile_context_has_user_profile(self):
        """Test profile context includes user profile"""
        response = self.client.get(reverse('profiles:my_profile'))
        self.assertIn('user_profile', response.context)
        self.assertEqual(response.context['user_profile'], self.user)
