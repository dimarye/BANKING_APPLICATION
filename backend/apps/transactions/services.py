from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.accounts.services import AccountService
from apps.accounts.models import BankAccount
from apps.fraud.services import FraudService, FraudDetectionError
from apps.transactions.models import Transaction
from apps.transactions.state_machine import TransactionStateMachine


class TransactionInProgressError(Exception):
    pass


class TransactionFailedError(Exception):
    def __init__(self, error_code: str | None, error_message: str | None):
        super().__init__(f"{error_code}: {error_message}")
        self.error_code = error_code
        self.error_message = error_message


class TransactionService:
    @staticmethod
    def process_transfer(
        idempotency_key: str,
        from_account_id: int,
        to_account_id: int,
        amount: Decimal,
        currency: str,
        description: str = "Transfer",
    ) -> Transaction:
        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to the same account")

        # Phase 1: create the Transaction and persist PENDING.
        # This ensures crash-safety: a process crash after this point leaves status=PENDING.
        with transaction.atomic():
            txn = (
                Transaction.objects.select_for_update()
                .filter(idempotency_key=idempotency_key)
                .first()
            )

            if txn is not None:
                if txn.status == Transaction.STATUS_COMPLETED:
                    return txn

                if txn.status == Transaction.STATUS_FAILED:
                    raise TransactionFailedError(txn.error_code, txn.error_message)

                if txn.status == Transaction.STATUS_PENDING:
                    raise TransactionInProgressError(
                        "Transaction is currently being processed. Please retry later."
                    )

                raise ValueError(f"Unexpected transaction status: {txn.status}")

            from_account = BankAccount.objects.get(id=from_account_id)
            to_account = BankAccount.objects.get(id=to_account_id)

            try:
                txn = Transaction.objects.create(
                    idempotency_key=idempotency_key,
                    from_account=from_account,
                    to_account=to_account,
                    amount=amount,
                    currency=currency,
                    status=Transaction.STATUS_CREATED,
                )
            except IntegrityError:
                # Most likely: another concurrent request created the row.
                # If not, re-raise (e.g. constraint violation like invalid amount/accounts).
                try:
                    txn = Transaction.objects.select_for_update().get(
                        idempotency_key=idempotency_key
                    )
                except Transaction.DoesNotExist:
                    raise
                if txn.status == Transaction.STATUS_COMPLETED:
                    return txn
                if txn.status == Transaction.STATUS_FAILED:
                    raise TransactionFailedError(txn.error_code, txn.error_message)
                raise TransactionInProgressError(
                    "Transaction is currently being processed. Please retry later."
                )

            # Evaluate fraud rules before transitioning to PENDING
            try:
                FraudService.evaluate_transaction(txn)
            except FraudDetectionError as e:
                # If fraud detection blocks the transaction, mark it as FAILED
                TransactionStateMachine.transition_to_failed(
                    txn,
                    e.rule_code,
                    e.reason,
                )
                raise TransactionFailedError(e.rule_code, e.reason)

            TransactionStateMachine.transition_to_pending(txn)

        # Phase 2: execute business logic under a lock and commit final status.
        # AccountService.transfer() runs under a nested atomic() savepoint; on exception,
        # its ledger writes are rolled back while we can still commit FAILED.
        exc: Exception | None = None
        with transaction.atomic():
            txn = Transaction.objects.select_for_update().get(
                idempotency_key=idempotency_key
            )

            if txn.status == Transaction.STATUS_COMPLETED:
                return txn
            if txn.status == Transaction.STATUS_FAILED:
                raise TransactionFailedError(txn.error_code, txn.error_message)
            if txn.status != Transaction.STATUS_PENDING:
                raise ValueError(f"Unexpected transaction status: {txn.status}")

            try:
                AccountService.transfer(
                    from_account_id=from_account_id,
                    to_account_id=to_account_id,
                    amount=amount,
                    description=description,
                )
                TransactionStateMachine.transition_to_completed(txn)
            except Exception as e:
                TransactionStateMachine.transition_to_failed(
                    txn,
                    type(e).__name__,
                    str(e),
                )
                exc = e

        if exc is not None:
            raise exc

        return txn
