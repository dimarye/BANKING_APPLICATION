from decimal import Decimal

from django.db import models

from apps.accounts.models import BankAccount


class Transaction(models.Model):
    STATUS_CREATED = "CREATED"
    STATUS_PENDING = "PENDING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)
    from_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="transactions_from",
    )
    to_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="transactions_to",
    )
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
    )
    error_code = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["idempotency_key"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["from_account", "status"]),
            models.Index(fields=["to_account", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="transaction_amount_positive",
            ),
            models.CheckConstraint(
                check=~models.Q(from_account=models.F("to_account")),
                name="transaction_different_accounts",
            ),
        ]

    def __str__(self):
        return f"Transaction {self.idempotency_key} ({self.status})"
