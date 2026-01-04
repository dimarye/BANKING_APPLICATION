from decimal import Decimal

from django.db import transaction
from django.db.models import Case, DecimalField, F, Sum, Value, When

from apps.accounts.models import Account, BankAccount, _BANK_ACCOUNT_LEDGER_TOKEN
from apps.ledger.models import LedgerEntry, _LEDGER_ENTRY_SERVICE_TOKEN


def get_account_balance(account: Account, currency: str) -> Decimal:
    currency_norm = currency.strip().upper()
    if currency_norm == "":
        raise ValueError("currency is required")

    account_currency_norm = account.currency.strip().upper()
    if account_currency_norm != currency_norm:
        raise ValueError("account currency mismatch")

    output_field = DecimalField(max_digits=18, decimal_places=4)

    aggregates = LedgerEntry.objects.filter(currency=currency_norm).aggregate(
        debit_sum=Sum(
            Case(
                When(debit_account=account, then=F("amount")),
                default=Value(0),
                output_field=output_field,
            )
        ),
        credit_sum=Sum(
            Case(
                When(credit_account=account, then=F("amount")),
                default=Value(0),
                output_field=output_field,
            )
        ),
    )

    debit_sum = aggregates.get("debit_sum") or Decimal("0")
    credit_sum = aggregates.get("credit_sum") or Decimal("0")

    return debit_sum - credit_sum


class LedgerService:
    @staticmethod
    def create_entry(
        *,
        debit_account: Account,
        credit_account: Account,
        amount: Decimal,
        currency: str,
        _account_service_token=None,
    ) -> LedgerEntry:
        touches_bank_account = BankAccount.objects.filter(
            ledger_account_id__in=[debit_account.id, credit_account.id]
        ).exists()
        if touches_bank_account and _account_service_token is not _BANK_ACCOUNT_LEDGER_TOKEN:
            raise RuntimeError("BankAccount ledger entries must be created via AccountService")

        if debit_account == credit_account:
            raise ValueError("debit_account and credit_account must be different")

        amount_dec = Decimal(str(amount))
        if amount_dec <= 0:
            raise ValueError("amount must be > 0")

        currency_norm = currency.strip().upper()
        if currency_norm == "":
            raise ValueError("currency is required")

        debit_currency_norm = debit_account.currency.strip().upper()
        if debit_currency_norm != currency_norm:
            raise ValueError("debit_account currency mismatch")

        credit_currency_norm = credit_account.currency.strip().upper()
        if credit_currency_norm != currency_norm:
            raise ValueError("credit_account currency mismatch")

        with transaction.atomic():
            entry = LedgerEntry(
                debit_account=debit_account,
                credit_account=credit_account,
                amount=amount_dec,
                currency=currency_norm,
            )
            entry.save(_service_token=_LEDGER_ENTRY_SERVICE_TOKEN)
            return entry
