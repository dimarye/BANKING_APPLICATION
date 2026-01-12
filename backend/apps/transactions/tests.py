from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase

from apps.accounts.models import Account, BankAccount
from apps.transactions.models import Transaction
from apps.transactions.state_machine import IllegalTransitionError, TransactionStateMachine

User = get_user_model()


class TransactionStateMachineTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        ledger_from = Account.objects.create(currency="USD")
        ledger_to = Account.objects.create(currency="USD")
        
        self.from_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_from,
        )
        self.to_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_to,
        )

    def test_transition_created_to_pending(self):
        txn = Transaction.objects.create(
            idempotency_key="test-key-1",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED,
        )
        
        TransactionStateMachine.transition_to_pending(txn)
        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.STATUS_PENDING)

    def test_transition_pending_to_completed(self):
        txn = Transaction.objects.create(
            idempotency_key="test-key-2",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_PENDING,
        )
        
        TransactionStateMachine.transition_to_completed(txn)
        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.STATUS_COMPLETED)

    def test_transition_pending_to_failed(self):
        txn = Transaction.objects.create(
            idempotency_key="test-key-3",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_PENDING,
        )
        
        TransactionStateMachine.transition_to_failed(txn, "INSUFFICIENT_FUNDS", "Not enough balance")
        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.STATUS_FAILED)
        self.assertEqual(txn.error_code, "INSUFFICIENT_FUNDS")
        self.assertEqual(txn.error_message, "Not enough balance")

    def test_illegal_transition_created_to_completed(self):
        txn = Transaction.objects.create(
            idempotency_key="test-key-4",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED,
        )
        
        with self.assertRaises(IllegalTransitionError):
            TransactionStateMachine.transition_to_completed(txn)

    def test_illegal_transition_created_to_failed(self):
        txn = Transaction.objects.create(
            idempotency_key="test-key-5",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_CREATED,
        )
        
        with self.assertRaises(IllegalTransitionError):
            TransactionStateMachine.transition_to_failed(txn, "ERROR", "Some error")

    def test_terminal_state_completed_cannot_transition(self):
        txn = Transaction.objects.create(
            idempotency_key="test-key-6",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_COMPLETED,
        )
        
        with self.assertRaises(IllegalTransitionError) as ctx:
            TransactionStateMachine.transition_to_pending(txn)
        self.assertIn("terminal state", str(ctx.exception))

    def test_terminal_state_failed_cannot_transition(self):
        txn = Transaction.objects.create(
            idempotency_key="test-key-7",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_FAILED,
        )
        
        with self.assertRaises(IllegalTransitionError) as ctx:
            TransactionStateMachine.transition_to_completed(txn)
        self.assertIn("terminal state", str(ctx.exception))

    def test_illegal_transition_pending_to_created(self):
        txn = Transaction.objects.create(
            idempotency_key="test-key-8",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_PENDING,
        )
        
        with self.assertRaises(IllegalTransitionError):
            TransactionStateMachine.validate_transition(Transaction.STATUS_PENDING, Transaction.STATUS_CREATED)


class TransactionServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

        from apps.accounts.services import AccountService
        
        ledger_from = Account.objects.create(currency="USD")
        ledger_to = Account.objects.create(currency="USD")
        
        self.from_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_BUSINESS,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            overdraft_limit=Decimal("1000.00"),
            ledger_account=ledger_from,
        )
        self.to_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_to,
        )

        AccountService.deposit(
            account_id=self.from_account.id,
            amount=Decimal("500.00"),
        )

    def test_process_transfer_success(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.services import get_account_balance
        from apps.ledger.models import LedgerEntry
        
        initial_from_balance = get_account_balance(self.from_account.ledger_account, "USD")
        initial_to_balance = get_account_balance(self.to_account.ledger_account, "USD")
        initial_entry_count = LedgerEntry.objects.count()
        
        txn = TransactionService.process_transfer(
            idempotency_key="transfer-001",
            from_account_id=self.from_account.id,
            to_account_id=self.to_account.id,
            amount=Decimal("100.00"),
            currency="USD",
        )
        
        self.assertEqual(txn.status, Transaction.STATUS_COMPLETED)
        self.assertEqual(txn.amount, Decimal("100.00"))
        self.assertIsNone(txn.error_code)
        
        final_from_balance = get_account_balance(self.from_account.ledger_account, "USD")
        final_to_balance = get_account_balance(self.to_account.ledger_account, "USD")
        final_entry_count = LedgerEntry.objects.count()
        
        self.assertEqual(final_from_balance, initial_from_balance - Decimal("100.00"))
        self.assertEqual(final_to_balance, initial_to_balance + Decimal("100.00"))
        self.assertEqual(final_entry_count, initial_entry_count + 1)

    def test_idempotency_completed_returns_same_transaction(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.services import get_account_balance
        from apps.ledger.models import LedgerEntry

        initial_balance = get_account_balance(self.from_account.ledger_account, "USD")
        initial_entry_count = LedgerEntry.objects.count()

        txn1 = TransactionService.process_transfer(
            idempotency_key="transfer-002",
            from_account_id=self.from_account.id,
            to_account_id=self.to_account.id,
            amount=Decimal("50.00"),
            currency="USD",
        )

        balance_after_first = get_account_balance(self.from_account.ledger_account, "USD")
        entry_count_after_first = LedgerEntry.objects.count()
        
        txn2 = TransactionService.process_transfer(
            idempotency_key="transfer-002",
            from_account_id=self.from_account.id,
            to_account_id=self.to_account.id,
            amount=Decimal("50.00"),
            currency="USD",
        )

        balance_after_second = get_account_balance(self.from_account.ledger_account, "USD")
        entry_count_after_second = LedgerEntry.objects.count()
        
        self.assertEqual(txn1.id, txn2.id)
        self.assertEqual(txn2.status, Transaction.STATUS_COMPLETED)
        self.assertEqual(balance_after_first, balance_after_second)
        self.assertEqual(entry_count_after_first, entry_count_after_second)
        self.assertEqual(balance_after_second, initial_balance - Decimal("50.00"))
        self.assertEqual(entry_count_after_second, initial_entry_count + 1)

    def test_idempotency_failed_raises_same_error(self):
        from apps.transactions.services import TransactionFailedError, TransactionService
        
        with self.assertRaises(Exception):
            TransactionService.process_transfer(
                idempotency_key="transfer-003",
                from_account_id=self.from_account.id,
                to_account_id=self.to_account.id,
                amount=Decimal("10000.00"),
                currency="USD",
            )
        
        txn = Transaction.objects.get(idempotency_key="transfer-003")
        self.assertEqual(txn.status, Transaction.STATUS_FAILED)
        self.assertIsNotNone(txn.error_code)

        with self.assertRaises(TransactionFailedError) as ctx:
            TransactionService.process_transfer(
                idempotency_key="transfer-003",
                from_account_id=self.from_account.id,
                to_account_id=self.to_account.id,
                amount=Decimal("10000.00"),
                currency="USD",
            )

        self.assertIn(txn.error_code, str(ctx.exception))

    def test_no_duplicate_transaction_created(self):
        from apps.transactions.services import TransactionService
        
        TransactionService.process_transfer(
            idempotency_key="transfer-004",
            from_account_id=self.from_account.id,
            to_account_id=self.to_account.id,
            amount=Decimal("25.00"),
            currency="USD",
        )
        
        TransactionService.process_transfer(
            idempotency_key="transfer-004",
            from_account_id=self.from_account.id,
            to_account_id=self.to_account.id,
            amount=Decimal("25.00"),
            currency="USD",
        )
        
        txn_count = Transaction.objects.filter(idempotency_key="transfer-004").count()
        self.assertEqual(txn_count, 1)

    def test_insufficient_funds_does_not_affect_ledger(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.services import get_account_balance
        from apps.ledger.models import LedgerEntry
        
        initial_from_balance = get_account_balance(self.from_account.ledger_account, "USD")
        initial_to_balance = get_account_balance(self.to_account.ledger_account, "USD")
        initial_entry_count = LedgerEntry.objects.count()
        
        with self.assertRaises(Exception):
            TransactionService.process_transfer(
                idempotency_key="transfer-005",
                from_account_id=self.from_account.id,
                to_account_id=self.to_account.id,
                amount=Decimal("10000.00"),
                currency="USD",
            )
        
        final_from_balance = get_account_balance(self.from_account.ledger_account, "USD")
        final_to_balance = get_account_balance(self.to_account.ledger_account, "USD")
        final_entry_count = LedgerEntry.objects.count()
        
        self.assertEqual(initial_from_balance, final_from_balance)
        self.assertEqual(initial_to_balance, final_to_balance)
        self.assertEqual(initial_entry_count, final_entry_count)
        
        txn = Transaction.objects.get(idempotency_key="transfer-005")
        self.assertEqual(txn.status, Transaction.STATUS_FAILED)
        self.assertIsNotNone(txn.error_code)

    def test_frozen_account_does_not_affect_ledger(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.services import get_account_balance
        from apps.ledger.models import LedgerEntry
        
        self.from_account.status = BankAccount.STATUS_FROZEN
        self.from_account.save()
        
        initial_from_balance = get_account_balance(self.from_account.ledger_account, "USD")
        initial_to_balance = get_account_balance(self.to_account.ledger_account, "USD")
        initial_entry_count = LedgerEntry.objects.count()
        
        with self.assertRaises(Exception):
            TransactionService.process_transfer(
                idempotency_key="transfer-006",
                from_account_id=self.from_account.id,
                to_account_id=self.to_account.id,
                amount=Decimal("50.00"),
                currency="USD",
            )
        
        final_from_balance = get_account_balance(self.from_account.ledger_account, "USD")
        final_to_balance = get_account_balance(self.to_account.ledger_account, "USD")
        final_entry_count = LedgerEntry.objects.count()
        
        self.assertEqual(initial_from_balance, final_from_balance)
        self.assertEqual(initial_to_balance, final_to_balance)
        self.assertEqual(initial_entry_count, final_entry_count)
        
        txn = Transaction.objects.get(idempotency_key="transfer-006")
        self.assertEqual(txn.status, Transaction.STATUS_FAILED)

    def test_same_account_transfer_does_not_affect_ledger(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.services import get_account_balance
        from apps.ledger.models import LedgerEntry
        
        initial_balance = get_account_balance(self.from_account.ledger_account, "USD")
        initial_entry_count = LedgerEntry.objects.count()
        
        with self.assertRaises(Exception):
            TransactionService.process_transfer(
                idempotency_key="transfer-007",
                from_account_id=self.from_account.id,
                to_account_id=self.from_account.id,
                amount=Decimal("50.00"),
                currency="USD",
            )
        
        final_balance = get_account_balance(self.from_account.ledger_account, "USD")
        final_entry_count = LedgerEntry.objects.count()
        
        self.assertEqual(initial_balance, final_balance)
        self.assertEqual(initial_entry_count, final_entry_count)

        self.assertFalse(Transaction.objects.filter(idempotency_key="transfer-007").exists())

    def test_transaction_atomicity_on_error(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.models import LedgerEntry
        
        initial_txn_count = Transaction.objects.count()
        initial_entry_count = LedgerEntry.objects.count()
        
        with self.assertRaises(Exception):
            TransactionService.process_transfer(
                idempotency_key="transfer-008",
                from_account_id=self.from_account.id,
                to_account_id=self.to_account.id,
                amount=Decimal("99999.00"),
                currency="USD",
            )
        
        final_txn_count = Transaction.objects.count()
        final_entry_count = LedgerEntry.objects.count()
        
        self.assertEqual(final_txn_count, initial_txn_count + 1)
        self.assertEqual(final_entry_count, initial_entry_count)
        
        txn = Transaction.objects.get(idempotency_key="transfer-008")
        self.assertEqual(txn.status, Transaction.STATUS_FAILED)

    def test_completed_transaction_ledger_entries_exist(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.models import LedgerEntry
        
        initial_entry_count = LedgerEntry.objects.count()
        
        txn = TransactionService.process_transfer(
            idempotency_key="transfer-009",
            from_account_id=self.from_account.id,
            to_account_id=self.to_account.id,
            amount=Decimal("75.00"),
            currency="USD",
        )
        
        final_entry_count = LedgerEntry.objects.count()
        
        self.assertEqual(txn.status, Transaction.STATUS_COMPLETED)
        self.assertGreater(final_entry_count, initial_entry_count)
        
        entries = LedgerEntry.objects.filter(
            currency="USD"
        ).order_by('-created_at')[:1]
        self.assertTrue(entries.exists())
        
        latest_entry = entries.first()
        self.assertEqual(latest_entry.amount, Decimal("75.00"))


class TransactionConcurrencyTestCase(TransactionTestCase):
    def setUp(self):
        from django.db import close_old_connections
        close_old_connections()
        
        self.user = User.objects.create_user(username="testuser", password="testpass")

        from apps.accounts.services import AccountService
        
        ledger_from = Account.objects.create(currency="USD")
        ledger_to = Account.objects.create(currency="USD")
        
        self.from_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_BUSINESS,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            overdraft_limit=Decimal("1000.00"),
            ledger_account=ledger_from,
        )
        self.to_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_to,
        )

        AccountService.deposit(
            account_id=self.from_account.id,
            amount=Decimal("500.00"),
        )

    def test_concurrent_same_idempotency_key_creates_single_transaction(self):
        from apps.transactions.services import TransactionService, TransactionInProgressError
        from apps.ledger.services import get_account_balance
        from django.db import close_old_connections
        import threading
        
        initial_balance = get_account_balance(self.from_account.ledger_account, "USD")
        results = []
        errors = []
        
        def process_transfer():
            close_old_connections()
            try:
                txn = TransactionService.process_transfer(
                    idempotency_key="concurrent-transfer-001",
                    from_account_id=self.from_account.id,
                    to_account_id=self.to_account.id,
                    amount=Decimal("100.00"),
                    currency="USD",
                )
                results.append(txn.id)
            except TransactionInProgressError:
                errors.append("in_progress")
            except Exception as e:
                errors.append(str(e))
            finally:
                close_old_connections()
        
        threads = [threading.Thread(target=process_transfer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        txn_count = Transaction.objects.filter(idempotency_key="concurrent-transfer-001").count()
        self.assertEqual(txn_count, 1)
        
        final_balance = get_account_balance(self.from_account.ledger_account, "USD")
        self.assertEqual(final_balance, initial_balance - Decimal("100.00"))
        
        completed_txn = Transaction.objects.get(idempotency_key="concurrent-transfer-001")
        self.assertEqual(completed_txn.status, Transaction.STATUS_COMPLETED)


class TransactionAtomicityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")

        from apps.accounts.services import AccountService
        
        ledger_from = Account.objects.create(currency="USD")
        ledger_to = Account.objects.create(currency="USD")
        
        self.from_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_BUSINESS,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            overdraft_limit=Decimal("1000.00"),
            ledger_account=ledger_from,
        )
        self.to_account = BankAccount.objects.create(
            user=self.user,
            account_type=BankAccount.ACCOUNT_TYPE_RETAIL,
            currency="USD",
            status=BankAccount.STATUS_ACTIVE,
            ledger_account=ledger_to,
        )

        AccountService.deposit(
            account_id=self.from_account.id,
            amount=Decimal("500.00"),
        )

    def test_ledger_and_transaction_status_in_same_db_transaction(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.services import get_account_balance
        from apps.ledger.models import LedgerEntry
        
        initial_balance = get_account_balance(self.from_account.ledger_account, "USD")
        initial_entry_count = LedgerEntry.objects.count()
        
        txn = TransactionService.process_transfer(
            idempotency_key="atomic-test-001",
            from_account_id=self.from_account.id,
            to_account_id=self.to_account.id,
            amount=Decimal("100.00"),
            currency="USD",
        )
        
        self.assertEqual(txn.status, Transaction.STATUS_COMPLETED)
        
        final_balance = get_account_balance(self.from_account.ledger_account, "USD")
        final_entry_count = LedgerEntry.objects.count()
        
        self.assertEqual(final_balance, initial_balance - Decimal("100.00"))
        self.assertGreater(final_entry_count, initial_entry_count)
        
        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.STATUS_COMPLETED)

    def test_crash_simulation_transaction_stays_pending(self):
        from apps.transactions.models import Transaction
        from apps.ledger.models import LedgerEntry
        from apps.ledger.services import get_account_balance
        
        initial_balance = get_account_balance(self.from_account.ledger_account, "USD")
        initial_entry_count = LedgerEntry.objects.count()
        
        txn = Transaction.objects.create(
            idempotency_key="crash-test-001",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_PENDING,
        )
        
        final_balance = get_account_balance(self.from_account.ledger_account, "USD")
        final_entry_count = LedgerEntry.objects.count()
        
        self.assertEqual(initial_balance, final_balance)
        self.assertEqual(initial_entry_count, final_entry_count)
        
        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.STATUS_PENDING)

    def test_retry_after_crash_returns_409(self):
        from apps.transactions.services import TransactionService, TransactionInProgressError
        
        Transaction.objects.create(
            idempotency_key="crash-test-002",
            from_account=self.from_account,
            to_account=self.to_account,
            amount=Decimal("100.00"),
            currency="USD",
            status=Transaction.STATUS_PENDING,
        )
        
        with self.assertRaises(TransactionInProgressError) as ctx:
            TransactionService.process_transfer(
                idempotency_key="crash-test-002",
                from_account_id=self.from_account.id,
                to_account_id=self.to_account.id,
                amount=Decimal("100.00"),
                currency="USD",
            )
        
        self.assertIn("retry later", str(ctx.exception).lower())

    def test_rollback_on_error_no_ledger_entry_created(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.models import LedgerEntry
        from django.db import transaction as db_transaction
        
        initial_entry_count = LedgerEntry.objects.count()
        initial_txn_count = Transaction.objects.count()
        
        with self.assertRaises(Exception):
            TransactionService.process_transfer(
                idempotency_key="rollback-test-001",
                from_account_id=self.from_account.id,
                to_account_id=self.to_account.id,
                amount=Decimal("99999.00"),
                currency="USD",
            )
        
        final_entry_count = LedgerEntry.objects.count()
        final_txn_count = Transaction.objects.count()
        
        self.assertEqual(initial_entry_count, final_entry_count)
        self.assertEqual(final_txn_count, initial_txn_count + 1)
        
        txn = Transaction.objects.get(idempotency_key="rollback-test-001")
        self.assertEqual(txn.status, Transaction.STATUS_FAILED)

    def test_all_or_nothing_ledger_and_status_update(self):
        from apps.transactions.services import TransactionService
        from apps.ledger.services import get_account_balance
        from apps.ledger.models import LedgerEntry
        
        initial_from_balance = get_account_balance(self.from_account.ledger_account, "USD")
        initial_to_balance = get_account_balance(self.to_account.ledger_account, "USD")
        initial_entry_count = LedgerEntry.objects.count()
        
        txn = TransactionService.process_transfer(
            idempotency_key="all-or-nothing-001",
            from_account_id=self.from_account.id,
            to_account_id=self.to_account.id,
            amount=Decimal("150.00"),
            currency="USD",
        )
        
        txn.refresh_from_db()
        final_from_balance = get_account_balance(self.from_account.ledger_account, "USD")
        final_to_balance = get_account_balance(self.to_account.ledger_account, "USD")
        final_entry_count = LedgerEntry.objects.count()
        
        if txn.status == Transaction.STATUS_COMPLETED:
            self.assertEqual(final_from_balance, initial_from_balance - Decimal("150.00"))
            self.assertEqual(final_to_balance, initial_to_balance + Decimal("150.00"))
            self.assertGreater(final_entry_count, initial_entry_count)
        elif txn.status == Transaction.STATUS_FAILED:
            self.assertEqual(final_from_balance, initial_from_balance)
            self.assertEqual(final_to_balance, initial_to_balance)
            self.assertEqual(final_entry_count, initial_entry_count)
        else:
            self.fail(f"Transaction in unexpected state: {txn.status}")
