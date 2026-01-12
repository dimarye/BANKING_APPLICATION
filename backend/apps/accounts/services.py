from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.accounts.models import Account, BankAccount, _BANK_ACCOUNT_LEDGER_TOKEN
from apps.ledger.services import LedgerService, get_account_balance


class InsufficientFundsError(Exception):
    pass


class AccountFrozenError(Exception):
    pass


class AccountClosedError(Exception):
    pass


class CurrencyMismatchError(Exception):
    pass


class SameAccountError(Exception):
    pass


class AccountService:
    @staticmethod
    def _check_account_active(  account: BankAccount) -> None:
        if account.status == BankAccount.STATUS_FROZEN:
            raise AccountFrozenError(f"Account {account.id} is frozen")
        if account.status == BankAccount.STATUS_CLOSED:
            raise AccountClosedError(f"Account {account.id} is closed")

    @staticmethod
    def _check_sufficient_funds(
        account: BankAccount,
        balance: Decimal,
        amount: Decimal,
    ) -> None:
        if account.account_type == BankAccount.ACCOUNT_TYPE_RETAIL:
            if balance < amount:
                raise InsufficientFundsError(
                    f"Insufficient funds: balance={balance}, required={amount}"
                )
        elif account.account_type == BankAccount.ACCOUNT_TYPE_BUSINESS:
            if balance - amount < -account.overdraft_limit:
                raise InsufficientFundsError(
                    f"Overdraft limit exceeded: balance={balance}, "
                    f"amount={amount}, limit={account.overdraft_limit}"
                )

    @staticmethod
    def _check_currency_consistency(account: BankAccount) -> None:
        account_currency = account.currency.strip().upper()
        ledger_currency = account.ledger_account.currency.strip().upper()
        if account_currency != ledger_currency:
            raise CurrencyMismatchError(
                f"Account currency mismatch: {account_currency} != {ledger_currency}"
            )

    @staticmethod
    def _get_system_account(currency: str) -> Account:
        try:
            system_account, _ = Account.objects.get_or_create(
                currency=currency,
                is_system=True,
                defaults={"currency": currency, "is_system": True},
            )
            return system_account
        except IntegrityError:
            return Account.objects.get(currency=currency, is_system=True)

    @staticmethod
    def withdraw(
        account_id: int,
        amount: Decimal,
        description: str = "Withdrawal",
    ) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        with transaction.atomic():
            account = BankAccount.objects.select_for_update().get(id=account_id)
            AccountService._check_account_active(account)
            AccountService._check_currency_consistency(account)

            balance = get_account_balance(account.ledger_account, account.currency)
            AccountService._check_sufficient_funds(account, balance, amount)

            system_account = AccountService._get_system_account(account.currency)

            LedgerService.create_entry(
                debit_account=system_account,
                credit_account=account.ledger_account,
                amount=amount,
                currency=account.currency,
                _account_service_token=_BANK_ACCOUNT_LEDGER_TOKEN,
            )

    @staticmethod
    def deposit(
        account_id: int,
        amount: Decimal,
        description: str = "Deposit",
    ) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        with transaction.atomic():
            account = BankAccount.objects.select_for_update().get(id=account_id)
            AccountService._check_account_active(account)
            AccountService._check_currency_consistency(account)

            system_account = AccountService._get_system_account(account.currency)

            LedgerService.create_entry(
                debit_account=account.ledger_account,
                credit_account=system_account,
                amount=amount,
                currency=account.currency,
                _account_service_token=_BANK_ACCOUNT_LEDGER_TOKEN,
            )

    @staticmethod
    def transfer(
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        description: str = "Transfer",
    ) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if from_account_id == to_account_id:
            raise SameAccountError("Cannot transfer to the same account")

        with transaction.atomic():
            if from_account_id < to_account_id:
                from_account = BankAccount.objects.select_for_update().get(
                    id=from_account_id
                )
                to_account = BankAccount.objects.select_for_update().get(
                    id=to_account_id
                )
            else:
                to_account = BankAccount.objects.select_for_update().get(
                    id=to_account_id
                )
                from_account = BankAccount.objects.select_for_update().get(
                    id=from_account_id
                )

            AccountService._check_account_active(from_account)
            AccountService._check_account_active(to_account)
            AccountService._check_currency_consistency(from_account)
            AccountService._check_currency_consistency(to_account)

            if from_account.currency != to_account.currency:
                raise CurrencyMismatchError(
                    f"Currency mismatch: {from_account.currency} != {to_account.currency}"
                )

            from_balance = get_account_balance(
                from_account.ledger_account, from_account.currency
            )
            AccountService._check_sufficient_funds(from_account, from_balance, amount)

            LedgerService.create_entry(
                debit_account=to_account.ledger_account,
                credit_account=from_account.ledger_account,
                amount=amount,
                currency=from_account.currency,
                _account_service_token=_BANK_ACCOUNT_LEDGER_TOKEN,
            )
