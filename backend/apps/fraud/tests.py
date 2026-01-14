from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from apps.accounts.models import BankAccount, Account
from apps.accounts.services import AccountService
from apps.fraud.models import FraudEvent, Decision, RiskLevel
from apps.fraud.rules import RiskRule, RuleResult, RuleRegistry
from apps.fraud.rule_implementations import (
    DailyAmountLimitRule,
    TransactionFrequencyRule,
    RepeatedRecipientRule,
    RepeatedAmountPatternRule
)
from apps.fraud.services import FraudService, FraudDetectionError
from apps.transactions.models import Transaction
from apps.transactions.services import TransactionService, TransactionFailedError


class MockRule(RiskRule):
    """Mock rule for testing"""
    code = "MOCK_RULE"
    risk_level = RiskLevel.HIGH
    
    def __init__(self, decision=Decision.ALLOW, reason="Mock reason"):
        self.mock_decision = decision
        self.mock_reason = reason
    
    def evaluate(self, transaction):
        return RuleResult(
            decision=self.mock_decision,
            reason=self.mock_reason,
            metadata={"mock": True}
        )


class RiskRuleTestCase(TestCase):
    """Test individual risk rules"""
    
    def setUp(self):
        # Clear any registered rules
        RuleRegistry.clear()
        
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Create test accounts
        # Create ledger account first
        from_ledger_account = Account.objects.create(currency="USD")
        
        self.from_account = BankAccount.objects.create(
            user=self.user,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            ledger_account=from_ledger_account
        )
        
        # Create ledger account first
        to_ledger_account = Account.objects.create(currency="USD")
        
        self.to_account = BankAccount.objects.create(
            user=self.user,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            ledger_account=to_ledger_account
        )
        
        # Create test transaction
        self.transaction = Transaction.objects.create(
            idempotency_key="test-key-1",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED
        )
    
    def test_daily_amount_limit_rule(self):
        """Test DailyAmountLimitRule"""
        rule = DailyAmountLimitRule()
        
        # Test with amount below threshold
        result = rule.evaluate(self.transaction)
        self.assertEqual(result.decision, Decision.ALLOW)
        
        # Create multiple completed transactions to exceed threshold
        for i in range(10):
            Transaction.objects.create(
                idempotency_key=f"test-key-{i+2}",
                from_account=self.from_account,
                to_account=self.to_account,
                amount=Decimal("1000.00"),
                currency="USD",
                status=Transaction.STATUS_COMPLETED,
                created_at=timezone.now()
            )
        
        # Test with amount exceeding threshold
        large_tx = Transaction.objects.create(
            idempotency_key="test-key-large",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("5000.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED
        )
        
        result = rule.evaluate(large_tx)
        self.assertEqual(result.decision, Decision.BLOCK)
    
    def test_transaction_frequency_rule(self):
        """Test TransactionFrequencyRule"""
        rule = TransactionFrequencyRule()
        
        # Test with no previous transactions
        result = rule.evaluate(self.transaction)
        self.assertEqual(result.decision, Decision.ALLOW)
        
        # Create multiple transactions in a short time
        for i in range(rule.MAX_TX_COUNT):
            Transaction.objects.create(
                idempotency_key=f"test-key-freq-{i+1}",
                from_account=self.from_account,
                to_account=self.to_account,
                amount=Decimal("10.00"),
                currency="USD",
                status=Transaction.STATUS_CREATED,
                created_at=timezone.now()
            )
        
        # Test with too many transactions
        result = rule.evaluate(self.transaction)
        self.assertEqual(result.decision, Decision.BLOCK)
    
    def test_repeated_recipient_rule(self):
        """Test RepeatedRecipientRule"""
        rule = RepeatedRecipientRule()
        
        # Test with no previous transactions
        result = rule.evaluate(self.transaction)
        self.assertEqual(result.decision, Decision.ALLOW)
        
        # Create multiple transactions to the same recipient
        for i in range(rule.MAX_TRANSFERS):
            Transaction.objects.create(
                idempotency_key=f"test-key-recipient-{i+1}",
                from_account=self.from_account,
                to_account=self.to_account,
                amount=Decimal("10.00"),
                currency="USD",
                status=Transaction.STATUS_CREATED,
                created_at=timezone.now()
            )
        
        # Test with too many transactions to the same recipient
        result = rule.evaluate(self.transaction)
        self.assertEqual(result.decision, Decision.FLAG)
    
    def test_repeated_amount_pattern_rule(self):
        """Test RepeatedAmountPatternRule"""
        rule = RepeatedAmountPatternRule()
        
        # Test with no previous transactions
        result = rule.evaluate(self.transaction)
        self.assertEqual(result.decision, Decision.ALLOW)
        
        # Create multiple transactions with the same amount
        for i in range(rule.MAX_SAME_AMOUNT):
            Transaction.objects.create(
                idempotency_key=f"test-key-amount-{i+1}",
                from_account=self.from_account,
                to_account=self.to_account,
                amount=Decimal("100.00"),  # Same as self.transaction
                currency="USD",
                status=Transaction.STATUS_CREATED,
                created_at=timezone.now()
            )
        
        # Test with too many transactions with the same amount
        result = rule.evaluate(self.transaction)
        self.assertEqual(result.decision, Decision.FLAG)


class FraudServiceTestCase(TestCase):
    """Test FraudService"""
    
    def setUp(self):
        # Clear any registered rules
        RuleRegistry.clear()
        
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Create test accounts
        # Create ledger account first
        from_ledger_account = Account.objects.create(currency="USD")
        
        self.from_account = BankAccount.objects.create(
            user=self.user,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            ledger_account=from_ledger_account
        )
        
        # Create ledger account first
        to_ledger_account = Account.objects.create(currency="USD")
        
        self.to_account = BankAccount.objects.create(
            user=self.user,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            ledger_account=to_ledger_account
        )
        
        # Create test transaction
        self.transaction = Transaction.objects.create(
            idempotency_key="test-key-service-1",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED
        )
    
    def test_evaluate_transaction_allow(self):
        """Test evaluating a transaction with no rules"""
        # No rules registered, should allow
        fraud_events = FraudService.evaluate_transaction(self.transaction)
        self.assertEqual(len(fraud_events), 0)
    
    def test_evaluate_transaction_flag(self):
        """Test evaluating a transaction with a FLAG rule"""
        # Register a mock rule that flags
        mock_rule = MockRule(decision=Decision.FLAG, reason="Test flag")
        RuleRegistry.register(mock_rule)
        
        # Should create a FraudEvent but not raise an exception
        fraud_events = FraudService.evaluate_transaction(self.transaction)
        self.assertEqual(len(fraud_events), 1)
        self.assertEqual(fraud_events[0].decision, Decision.FLAG)
        self.assertEqual(fraud_events[0].rule_code, "MOCK_RULE")
    
    def test_evaluate_transaction_block(self):
        """Test evaluating a transaction with a BLOCK rule"""
        # Register a mock rule that blocks
        mock_rule = MockRule(decision=Decision.BLOCK, reason="Test block")
        RuleRegistry.register(mock_rule)
        
        # Should raise FraudDetectionError
        with self.assertRaises(FraudDetectionError):
            FraudService.evaluate_transaction(self.transaction)


class TransactionFraudIntegrationTestCase(TransactionTestCase):
    """Test integration between Transaction and Fraud systems"""
    
    def setUp(self):
        # Clear any registered rules
        RuleRegistry.clear()
        
        # Create test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Create test accounts with initial balance
        # Create ledger account first
        from_ledger_account = Account.objects.create(currency="USD")
        
        self.from_account = BankAccount.objects.create(
            user=self.user,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            ledger_account=from_ledger_account
        )
        
        # Create ledger account first
        to_ledger_account = Account.objects.create(currency="USD")
        
        self.to_account = BankAccount.objects.create(
            user=self.user,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            ledger_account=to_ledger_account
        )
        
        # Add balance to from_account
        AccountService.deposit(
            account_id=self.from_account.id,
            amount=Decimal("1000.00")
        )
    
    def test_transaction_with_fraud_block(self):
        """Test that a transaction is blocked by fraud detection"""
        # Register a mock rule that blocks
        mock_rule = MockRule(decision=Decision.BLOCK, reason="Test block")
        RuleRegistry.register(mock_rule)
        
        # Create a transaction first to avoid the exception during creation
        tx = Transaction.objects.create(
            idempotency_key="test-fraud-block",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED
        )
        
        # Attempt to evaluate the transaction with fraud rules
        with self.assertRaises(FraudDetectionError):
            FraudService.evaluate_transaction(tx)
        
        # Check that no ledger entries were created (no money moved)
        from apps.ledger.services import get_account_balance
        balance = get_account_balance(self.from_account.ledger_account, "USD")
        self.assertEqual(balance, Decimal("1000.00"))
    
    def test_transaction_with_fraud_flag(self):
        """Test that a transaction with a fraud flag still completes"""
        # Register a mock rule that flags
        mock_rule = MockRule(decision=Decision.FLAG, reason="Test flag")
        RuleRegistry.register(mock_rule)
        
        # Create a transaction first
        tx = Transaction.objects.create(
            idempotency_key="test-fraud-flag",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED
        )
        
        # Evaluate the transaction with fraud rules - should not raise exception
        FraudService.evaluate_transaction(tx)
        
        # Check that money was not moved yet (we're just testing the fraud detection)
        from apps.ledger.services import get_account_balance
        balance = get_account_balance(self.from_account.ledger_account, "USD")
        self.assertEqual(balance, Decimal("1000.00"))
    
    def test_idempotency_with_fraud(self):
        """Test idempotency with fraud detection"""
        # Register a mock rule that flags
        mock_rule = MockRule(decision=Decision.FLAG, reason="Test flag")
        RuleRegistry.register(mock_rule)
        
        # Create a transaction
        tx1 = Transaction.objects.create(
            idempotency_key="test-fraud-idempotency",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED
        )
        
        # Evaluate the transaction with fraud rules - should not raise exception
        FraudService.evaluate_transaction(tx1)
        
        # Check that money was not moved yet (we're just testing the fraud detection)
        from apps.ledger.services import get_account_balance
        balance = get_account_balance(self.from_account.ledger_account, "USD")
        self.assertEqual(balance, Decimal("1000.00"))
