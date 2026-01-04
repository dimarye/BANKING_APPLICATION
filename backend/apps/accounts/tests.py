import threading
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase

from apps.accounts.models import Account, BankAccount
from apps.accounts.services import (
    AccountClosedError,
    AccountFrozenError,
    AccountService,
    CurrencyMismatchError,
    InsufficientFundsError,
    SameAccountError,
)
from apps.ledger.services import LedgerService
from apps.ledger.services import get_account_balance

User = get_user_model()


class AccountServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="test123")
        
        self.ledger_account_usd = Account.objects.create(currency="USD")
        self.bank_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=self.ledger_account_usd,
        )

    def test_deposit_success(self):
        AccountService.deposit(self.bank_account.id, Decimal("100"))
        
        balance = get_account_balance(self.ledger_account_usd, "USD")
        self.assertEqual(balance, Decimal("100"))

    def test_withdraw_success(self):
        AccountService.deposit(self.bank_account.id, Decimal("100"))
        AccountService.withdraw(self.bank_account.id, Decimal("30"))
        
        balance = get_account_balance(self.ledger_account_usd, "USD")
        self.assertEqual(balance, Decimal("70"))

    def test_transfer_success(self):
        ledger_account_2 = Account.objects.create(currency="USD")
        bank_account_2 = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_account_2,
        )

        AccountService.deposit(self.bank_account.id, Decimal("100"))
        AccountService.transfer(
            self.bank_account.id,
            bank_account_2.id,
            Decimal("40"),
        )

        balance_1 = get_account_balance(self.ledger_account_usd, "USD")
        balance_2 = get_account_balance(ledger_account_2, "USD")
        
        self.assertEqual(balance_1, Decimal("60"))
        self.assertEqual(balance_2, Decimal("40"))

    def test_retail_account_cannot_go_negative(self):
        AccountService.deposit(self.bank_account.id, Decimal("50"))
        
        with self.assertRaises(InsufficientFundsError):
            AccountService.withdraw(self.bank_account.id, Decimal("60"))
        
        balance = get_account_balance(self.ledger_account_usd, "USD")
        self.assertEqual(balance, Decimal("50"))

    def test_business_account_can_use_overdraft(self):
        ledger_account_biz = Account.objects.create(currency="USD")
        bank_account_biz = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_BUSINESS,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            overdraft_limit=Decimal("100"),
            ledger_account=ledger_account_biz,
        )

        AccountService.deposit(bank_account_biz.id, Decimal("50"))
        AccountService.withdraw(bank_account_biz.id, Decimal("120"))
        
        balance = get_account_balance(ledger_account_biz, "USD")
        self.assertEqual(balance, Decimal("-70"))

    def test_business_account_overdraft_limit_enforced(self):
        ledger_account_biz = Account.objects.create(currency="USD")
        bank_account_biz = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_BUSINESS,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            overdraft_limit=Decimal("100"),
            ledger_account=ledger_account_biz,
        )

        AccountService.deposit(bank_account_biz.id, Decimal("50"))
        
        with self.assertRaises(InsufficientFundsError):
            AccountService.withdraw(bank_account_biz.id, Decimal("200"))
        
        balance = get_account_balance(ledger_account_biz, "USD")
        self.assertEqual(balance, Decimal("50"))

    def test_frozen_account_blocks_operations(self):
        self.bank_account.status = BankAccount.STATUS_FROZEN
        self.bank_account.save()

        with self.assertRaises(AccountFrozenError):
            AccountService.deposit(self.bank_account.id, Decimal("100"))

        with self.assertRaises(AccountFrozenError):
            AccountService.withdraw(self.bank_account.id, Decimal("10"))

    def test_closed_account_blocks_operations(self):
        self.bank_account.status = BankAccount.STATUS_CLOSED
        self.bank_account.save()

        with self.assertRaises(AccountClosedError):
            AccountService.deposit(self.bank_account.id, Decimal("100"))

    def test_transfer_currency_mismatch(self):
        ledger_account_eur = Account.objects.create(currency="EUR")
        bank_account_eur = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="EUR",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_account_eur,
        )

        AccountService.deposit(self.bank_account.id, Decimal("100"))

        with self.assertRaises(CurrencyMismatchError):
            AccountService.transfer(
                self.bank_account.id,
                bank_account_eur.id,
                Decimal("50"),
            )

    def test_transfer_to_same_account(self):
        AccountService.deposit(self.bank_account.id, Decimal("100"))

        with self.assertRaises(SameAccountError):
            AccountService.transfer(
                self.bank_account.id,
                self.bank_account.id,
                Decimal("50"),
            )

    def test_negative_amount_rejected(self):
        with self.assertRaises(ValueError):
            AccountService.deposit(self.bank_account.id, Decimal("-10"))

        with self.assertRaises(ValueError):
            AccountService.withdraw(self.bank_account.id, Decimal("-10"))

        with self.assertRaises(ValueError):
            AccountService.transfer(
                self.bank_account.id,
                self.bank_account.id,
                Decimal("-10"),
            )

    def test_direct_ledger_entry_for_bank_accounts_is_forbidden(self):
        ledger_account_2 = Account.objects.create(currency="USD")
        bank_account_2 = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_account_2,
        )

        with self.assertRaises(RuntimeError):
            LedgerService.create_entry(
                debit_account=self.ledger_account_usd,
                credit_account=ledger_account_2,
                amount=Decimal("1"),
                currency="USD",
            )


class ConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="test123")
        
        self.ledger_account = Account.objects.create(currency="USD")
        self.bank_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=self.ledger_account,
        )
        
        AccountService.deposit(self.bank_account.id, Decimal("100"))

    def test_concurrent_withdrawals_serialized(self):
        errors = []

        def withdraw_50():
            close_old_connections()
            try:
                AccountService.withdraw(self.bank_account.id, Decimal("60"))
            except InsufficientFundsError as e:
                errors.append(e)
            finally:
                close_old_connections()

        thread1 = threading.Thread(target=withdraw_50)
        thread2 = threading.Thread(target=withdraw_50)

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        self.assertEqual(len(errors), 1)
        
        balance = get_account_balance(self.ledger_account, "USD")
        self.assertEqual(balance, Decimal("40"))

    def test_concurrent_transfers_maintain_consistency(self):
        ledger_account_2 = Account.objects.create(currency="USD")
        bank_account_2 = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_account_2,
        )

        def transfer_30():
            close_old_connections()
            try:
                AccountService.transfer(
                    self.bank_account.id,
                    bank_account_2.id,
                    Decimal("30"),
                )
            except InsufficientFundsError:
                pass
            finally:
                close_old_connections()

        thread1 = threading.Thread(target=transfer_30)
        thread2 = threading.Thread(target=transfer_30)
        thread3 = threading.Thread(target=transfer_30)

        thread1.start()
        thread2.start()
        thread3.start()
        thread1.join()
        thread2.join()
        thread3.join()

        balance_1 = get_account_balance(self.ledger_account, "USD")
        balance_2 = get_account_balance(ledger_account_2, "USD")
        
        total = balance_1 + balance_2
        self.assertEqual(total, Decimal("100"))
        
        self.assertGreaterEqual(balance_1, Decimal("0"))
