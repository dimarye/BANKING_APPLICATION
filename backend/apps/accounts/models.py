from decimal import Decimal

from django.conf import settings
from django.db import models


class Account(models.Model):
    currency = models.CharField(max_length=3)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["currency"]),
            models.Index(fields=["currency", "is_system"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["currency", "is_system"],
                condition=models.Q(is_system=True),
                name="unique_system_account_per_currency",
            ),
        ]


class BankAccount(models.Model):
    ACCOUNT_TYPE_RETAIL = "RETAIL"
    ACCOUNT_TYPE_BUSINESS = "BUSINESS"
    ACCOUNT_TYPE_CHOICES = [
        (ACCOUNT_TYPE_RETAIL, "Retail"),
        (ACCOUNT_TYPE_BUSINESS, "Business"),
    ]

    STATUS_ACTIVE = "ACTIVE"
    STATUS_FROZEN = "FROZEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_FROZEN, "Frozen"),
        (STATUS_CLOSED, "Closed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bank_accounts",
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default=ACCOUNT_TYPE_RETAIL,
    )
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )
    overdraft_limit = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=Decimal("0"),
    )
    ledger_account = models.OneToOneField(
        Account,
        on_delete=models.PROTECT,
        related_name="bank_account",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["currency"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(overdraft_limit__gte=0),
                name="bank_account_overdraft_limit_gte_zero",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(account_type="RETAIL", overdraft_limit=0)
                    | models.Q(account_type="BUSINESS")
                ),
                name="bank_account_retail_no_overdraft",
            ),
        ]


_BANK_ACCOUNT_LEDGER_TOKEN = object()
