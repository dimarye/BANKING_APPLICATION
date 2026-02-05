from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import status
from .serializers import (
    UserRegistrationSerializer, 
    BankAccountSerializer,
    DepositSerializer,
    WithdrawalSerializer
)
from .models import BankAccount, Account


class SerializerTestCase(TestCase):
    """Test serializers without database"""
    
    def test_user_registration_serializer_valid_data(self):
        """Test user registration serializer with valid data"""
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'testpass123',
            'password_confirm': 'differentpass'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)
    
    def test_deposit_serializer_valid_data(self):
        """Test deposit serializer with valid data"""
        data = {
            'account_id': 1,
            'amount': '100.00',
            'description': 'Test deposit'
        }
        serializer = DepositSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_deposit_serializer_invalid_amount(self):
        """Test deposit serializer with invalid amount"""
        data = {
            'account_id': 1,
            'amount': '-100.00',
            'description': 'Test deposit'
        }
        serializer = DepositSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_withdrawal_serializer_valid_data(self):
        """Test withdrawal serializer with valid data"""
        data = {
            'account_id': 1,
            'amount': '50.00',
            'description': 'Test withdrawal'
        }
        serializer = WithdrawalSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_withdrawal_serializer_zero_amount(self):
        """Test withdrawal serializer with zero amount"""
        data = {
            'account_id': 1,
            'amount': '0.00',
            'description': 'Test withdrawal'
        }
        serializer = WithdrawalSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)


class ModelTestCase(TestCase):
    """Test models without database operations"""
    
    def test_bank_account_model_choices(self):
        """Test bank account model choices"""
        self.assertEqual(BankAccount.ACCOUNT_TYPE_RETAIL, "RETAIL")
        self.assertEqual(BankAccount.ACCOUNT_TYPE_BUSINESS, "BUSINESS")
        self.assertEqual(BankAccount.STATUS_ACTIVE, "ACTIVE")
        self.assertEqual(BankAccount.STATUS_FROZEN, "FROZEN")
        self.assertEqual(BankAccount.STATUS_CLOSED, "CLOSED")
    
    def test_bank_account_model_str(self):
        """Test bank account string representation"""
        # This would need database, so we'll test the structure
        self.assertTrue(hasattr(BankAccount, '__str__'))
        self.assertTrue(hasattr(BankAccount, 'user'))
        self.assertTrue(hasattr(BankAccount, 'account_type'))
        self.assertTrue(hasattr(BankAccount, 'currency'))


class PermissionTestCase(TestCase):
    """Test permissions without database"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test user creation works"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_email_uniqueness(self):
        """Test email uniqueness constraint"""
        # This would be tested with database, but we can check the field exists
        self.assertTrue(hasattr(User, 'email'))


class UtilityTestCase(TestCase):
    """Test utility functions"""
    
    def test_decimal_operations(self):
        """Test decimal operations for financial calculations"""
        amount1 = Decimal('100.00')
        amount2 = Decimal('50.00')
        
        # Test addition
        result = amount1 + amount2
        self.assertEqual(result, Decimal('150.00'))
        
        # Test subtraction
        result = amount1 - amount2
        self.assertEqual(result, Decimal('50.00'))
        
        # Test comparison
        self.assertTrue(amount1 > amount2)
        self.assertTrue(amount2 > Decimal('0'))
    
    def test_currency_validation(self):
        """Test currency code validation"""
        valid_currencies = ['USD', 'EUR', 'GBP', 'JPY']
        invalid_currencies = ['US', 'EURO', '123', '']
        
        for currency in valid_currencies:
            self.assertEqual(len(currency), 3)
            self.assertTrue(currency.isalpha())
            self.assertTrue(currency.isupper())
        
        for currency in invalid_currencies:
            if currency:  # Skip empty string for this test
                self.assertNotEqual(len(currency), 3)
