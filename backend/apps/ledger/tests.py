from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import Account
from apps.ledger.models import LedgerEntry
from apps.ledger.services import LedgerService, get_account_balance


class LedgerServiceTests(TestCase):
    def setUp(self):
        self.a1 = Account.objects.create(currency="USD")
        self.a2 = Account.objects.create(currency="USD")

    def test_create_entry_success(self):
        LedgerService.create_entry(
            debit_account=self.a1,
            credit_account=self.a2,
            amount=Decimal("100"),
            currency="USD",
        )

        self.assertEqual(LedgerEntry.objects.count(), 1)

    def test_balance_math(self):
        LedgerService.create_entry(
            debit_account=self.a1,
            credit_account=self.a2,
            amount=Decimal("100"),
            currency="USD",
        )
        LedgerService.create_entry(
            debit_account=self.a2,
            credit_account=self.a1,
            amount=Decimal("30"),
            currency="USD",
        )

        self.assertEqual(get_account_balance(self.a1, "USD"), Decimal("70"))
        self.assertEqual(get_account_balance(self.a2, "USD"), Decimal("-70"))

        total = get_account_balance(self.a1, "USD") + get_account_balance(self.a2, "USD")
        self.assertEqual(total, Decimal("0"))

    def test_get_account_balance_currency_mismatch(self):
        with self.assertRaises(ValueError):
            get_account_balance(self.a1, "EUR")

    def test_create_entry_normalizes_currency(self):
        LedgerService.create_entry(
            debit_account=self.a1,
            credit_account=self.a2,
            amount=Decimal("1"),
            currency=" usd ",
        )

        entry = LedgerEntry.objects.get()
        self.assertEqual(entry.currency, "USD")

    def test_amount_must_be_positive(self):
        with self.assertRaises(ValueError):
            LedgerService.create_entry(
                debit_account=self.a1,
                credit_account=self.a2,
                amount=Decimal("0"),
                currency="USD",
            )

        with self.assertRaises(ValueError):
            LedgerService.create_entry(
                debit_account=self.a1,
                credit_account=self.a2,
                amount=Decimal("-1"),
                currency="USD",
            )

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_accounts_must_be_different(self):
        with self.assertRaises(ValueError):
            LedgerService.create_entry(
                debit_account=self.a1,
                credit_account=self.a1,
                amount=Decimal("1"),
                currency="USD",
            )

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_currency_must_match_both_accounts(self):
        eur = Account.objects.create(currency="EUR")

        with self.assertRaises(ValueError):
            LedgerService.create_entry(
                debit_account=self.a1,
                credit_account=eur,
                amount=Decimal("1"),
                currency="USD",
            )

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_direct_save_is_forbidden(self):
        entry = LedgerEntry(
            debit_account=self.a1,
            credit_account=self.a2,
            amount=Decimal("1"),
            currency="USD",
        )

        with self.assertRaises(RuntimeError):
            entry.save()

        with self.assertRaises(RuntimeError):
            entry.save(_via_service=True)

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_direct_manager_create_is_forbidden(self):
        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.create(
                debit_account=self.a1,
                credit_account=self.a2,
                amount=Decimal("1"),
                currency="USD",
            )

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_direct_manager_bulk_create_is_forbidden(self):
        entry = LedgerEntry(
            debit_account=self.a1,
            credit_account=self.a2,
            amount=Decimal("1"),
            currency="USD",
        )

        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.bulk_create([entry])

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_direct_manager_get_or_create_is_forbidden(self):
        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.get_or_create(
                debit_account=self.a1,
                credit_account=self.a2,
                amount=Decimal("1"),
                currency="USD",
            )

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_direct_manager_update_or_create_is_forbidden(self):
        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.update_or_create(
                debit_account=self.a1,
                credit_account=self.a2,
                defaults={"amount": Decimal("1"), "currency": "USD"},
            )

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_base_manager_create_is_forbidden(self):
        with self.assertRaises(RuntimeError):
            LedgerEntry._base_manager.create(
                debit_account=self.a1,
                credit_account=self.a2,
                amount=Decimal("1"),
                currency="USD",
            )

        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_entries_are_immutable(self):
        entry = LedgerService.create_entry(
            debit_account=self.a1,
            credit_account=self.a2,
            amount=Decimal("10"),
            currency="USD",
        )

        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.filter(id=entry.id).update(amount=Decimal("11"))

        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.filter(id=entry.id).delete()

        with self.assertRaises(RuntimeError):
            entry.delete()

    def test_bulk_update_is_forbidden(self):
        entry = LedgerService.create_entry(
            debit_account=self.a1,
            credit_account=self.a2,
            amount=Decimal("10"),
            currency="USD",
        )

        entry.amount = Decimal("11")

        with self.assertRaises(RuntimeError):
            LedgerEntry.objects.bulk_update([entry], ["amount"])

    def test_sum_of_all_balances_is_zero(self):
        a3 = Account.objects.create(currency="USD")

        LedgerService.create_entry(
            debit_account=self.a1,
            credit_account=self.a2,
            amount=Decimal("100"),
            currency="USD",
        )
        LedgerService.create_entry(
            debit_account=self.a2,
            credit_account=a3,
            amount=Decimal("40"),
            currency="USD",
        )
        LedgerService.create_entry(
            debit_account=a3,
            credit_account=self.a1,
            amount=Decimal("10"),
            currency="USD",
        )

        total = (
            get_account_balance(self.a1, "USD")
            + get_account_balance(self.a2, "USD")
            + get_account_balance(a3, "USD")
        )
        self.assertEqual(total, Decimal("0"))
