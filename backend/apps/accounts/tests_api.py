from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import BankAccount


class AuthenticationAPITestCase(APITestCase):
    """Test authentication endpoints"""
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('accounts:register')
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
    
    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        url = reverse('accounts:register')
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'testpass123',
            'password_confirm': 'differentpass'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='test@example.com').exists())
    
    def test_user_login(self):
        """Test user login endpoint"""
        # Create user first
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        
        url = reverse('accounts:login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('accounts:login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BankAccountAPITestCase(APITestCase):
    """Test bank account endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_bank_account(self):
        """Test creating a bank account"""
        url = reverse('accounts:account-list')
        data = {
            'account_type': 'RETAIL',
            'currency': 'USD',
            'overdraft_limit': '100.00'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BankAccount.objects.count(), 1)
        self.assertEqual(BankAccount.objects.first().user, self.user)
    
    def test_list_bank_accounts(self):
        """Test listing user's bank accounts"""
        # Create a bank account first via API
        url = reverse('accounts:account-list')
        data = {
            'account_type': 'RETAIL',
            'currency': 'USD',
            'overdraft_limit': '100.00'
        }
        self.client.post(url, data, format='json')
        
        url = reverse('accounts:account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_get_bank_account_detail(self):
        """Test getting bank account details"""
        # Create a bank account first via API
        url = reverse('accounts:account-list')
        data = {
            'account_type': 'RETAIL',
            'currency': 'USD',
            'overdraft_limit': '100.00'
        }
        response = self.client.post(url, data, format='json')
        account_id = response.data['id']
        
        url = reverse('accounts:account-detail', kwargs={'pk': account_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], account_id)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access accounts"""
        self.client.force_authenticate(user=None)
        
        url = reverse('accounts:account-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TransactionAPITestCase(APITestCase):
    """Test transaction endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create bank accounts via API
        self.client.force_authenticate(user=self.user1)
        
        # Create account for user1
        url = reverse('accounts:account-list')
        data = {
            'account_type': 'RETAIL',
            'currency': 'USD',
            'overdraft_limit': '100.00'
        }
        response = self.client.post(url, data, format='json')
        self.account1_id = response.data['id']
        
        # Create account for user2
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(url, data, format='json')
        self.account2_id = response.data['id']
        
        # Switch back to user1
        self.client.force_authenticate(user=self.user1)
    
    def test_transfer_money(self):
        """Test money transfer endpoint"""
        # First deposit some money
        url = reverse('accounts:deposit')
        data = {
            'account_id': self.account1_id,
            'amount': '1000.00',
            'description': 'Initial deposit'
        }
        self.client.post(url, data, format='json')
        
        # Now transfer money
        url = reverse('accounts:transfer')
        data = {
            'from_account_id': self.account1_id,
            'to_account_id': self.account2_id,
            'amount': '100.00',
            'currency': 'USD',
            'description': 'Test transfer'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['amount'], '100.00')
    
    def test_transfer_insufficient_funds(self):
        """Test transfer with insufficient funds"""
        url = reverse('accounts:transfer')
        data = {
            'from_account_id': self.account1_id,
            'to_account_id': self.account2_id,
            'amount': '2000.00',  # More than balance
            'currency': 'USD'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'INSUFFICIENT_FUNDS')
    
    def test_transfer_to_same_account(self):
        """Test transfer to same account should fail"""
        url = reverse('accounts:transfer')
        data = {
            'from_account_id': self.account1_id,
            'to_account_id': self.account1_id,  # Same account
            'amount': '100.00',
            'currency': 'USD'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_deposit_money(self):
        """Test deposit endpoint"""
        url = reverse('accounts:deposit')
        data = {
            'account_id': self.account1_id,
            'amount': '500.00',
            'description': 'Test deposit'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_withdraw_money(self):
        """Test withdrawal endpoint"""
        # First deposit some money
        url = reverse('accounts:deposit')
        data = {
            'account_id': self.account1_id,
            'amount': '200.00',
            'description': 'Deposit for withdrawal'
        }
        self.client.post(url, data, format='json')
        
        # Now withdraw
        url = reverse('accounts:withdraw')
        data = {
            'account_id': self.account1_id,
            'amount': '100.00',
            'description': 'Test withdrawal'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_withdraw_insufficient_funds(self):
        """Test withdrawal with insufficient funds"""
        url = reverse('accounts:withdraw')
        data = {
            'account_id': self.account1_id,
            'amount': '2000.00',  # More than balance
            'description': 'Test withdrawal'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'INSUFFICIENT_FUNDS')


class RateLimitingTestCase(APITestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_login_rate_limiting(self):
        """Test that login endpoint is rate limited"""
        url = reverse('accounts:login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        
        # Make multiple failed login attempts
        for i in range(6):  # Exceed the rate limit of 5/m
            response = self.client.post(url, data, format='json')
        
        # The last request should be rate limited
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
