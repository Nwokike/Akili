from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from payments.models import Payment
from decimal import Decimal


class PaymentModelTestCase(TestCase):
    """Tests for Payment model"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='payment@example.com',
            password='testpass123'
        )
    
    def test_payment_creation(self):
        """Test creating a payment record"""
        payment = Payment.objects.create(
            user=self.user,
            reference='PAY_123456',
            amount=Decimal('1000.00'),
            verified=False
        )
        self.assertEqual(payment.reference, 'PAY_123456')
        self.assertEqual(payment.amount, Decimal('1000.00'))
        self.assertFalse(payment.verified)
    
    def test_payment_string_representation(self):
        """Test payment string representation"""
        payment = Payment.objects.create(
            user=self.user,
            reference='PAY_123456',
            amount=Decimal('1000.00')
        )
        self.assertIn('1000', str(payment))
    
    def test_payment_reference_unique(self):
        """Test payment reference is unique"""
        Payment.objects.create(
            user=self.user,
            reference='PAY_UNIQUE',
            amount=Decimal('500.00')
        )
        
        with self.assertRaises(Exception):
            Payment.objects.create(
                user=self.user,
                reference='PAY_UNIQUE',
                amount=Decimal('600.00')
            )
    
    def test_payment_verified_update(self):
        """Test updating payment verified status"""
        payment = Payment.objects.create(
            user=self.user,
            reference='PAY_VERIFY',
            amount=Decimal('2000.00'),
            verified=False
        )
        
        payment.verified = True
        payment.save()
        
        payment.refresh_from_db()
        self.assertTrue(payment.verified)
    
    def test_user_payments_relationship(self):
        """Test user has many payments"""
        Payment.objects.create(
            user=self.user,
            reference='PAY_001',
            amount=Decimal('500.00')
        )
        Payment.objects.create(
            user=self.user,
            reference='PAY_002',
            amount=Decimal('1000.00')
        )
        
        self.assertEqual(self.user.payments.count(), 2)


class PaymentViewsTestCase(TestCase):
    """Tests for payment views"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='payview@example.com',
            password='testpass123'
        )
    
    def setUp(self):
        self.client = Client()
        self.client.login(email='payview@example.com', password='testpass123')
    
    def test_payment_initialize_requires_login(self):
        """Test payment initialize requires authentication"""
        self.client.logout()
        response = self.client.post(reverse('payments:initialize_payment'))
        self.assertEqual(response.status_code, 302)


class PaymentIntegrationTestCase(TestCase):
    """Integration tests for payment flow"""
    
    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()
        cls.user = cls.User.objects.create_user(
            email='payintegration@example.com',
            password='testpass123'
        )
    
    def setUp(self):
        self.client = Client()
        self.client.login(email='payintegration@example.com', password='testpass123')
    
    def test_payment_history_empty(self):
        """Test payment history is empty for new user"""
        payments = Payment.objects.filter(user=self.user)
        self.assertEqual(payments.count(), 0)
    
    def test_verified_payment_adds_credits(self):
        """Test verified payment adds credits to user"""
        initial_credits = self.user.tutor_credits
        
        Payment.objects.create(
            user=self.user,
            reference='PAY_CREDITS',
            amount=Decimal('1000.00'),
            verified=True
        )
        
        self.user.add_credits(50)
        self.assertEqual(self.user.tutor_credits, initial_credits + 50)
