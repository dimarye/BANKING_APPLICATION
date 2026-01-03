from django.db import models
from django.db.models import F, Q


_LEDGER_ENTRY_SERVICE_TOKEN = object()


class LedgerEntryQuerySet(models.QuerySet):
    def create(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry must be created via LedgerService")

    def bulk_create(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry must be created via LedgerService")

    def get_or_create(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry must be created via LedgerService")

    def update_or_create(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry must be created via LedgerService")

    def update(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry is immutable")

    def delete(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry is immutable")


class LedgerEntryManager(models.Manager.from_queryset(LedgerEntryQuerySet)):
    def create(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry must be created via LedgerService")

    def bulk_create(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry must be created via LedgerService")

    def bulk_update(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry is immutable")

    def get_or_create(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry must be created via LedgerService")

    def update_or_create(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry must be created via LedgerService")


class LedgerEntry(models.Model):
    debit_account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="debit_entries",
    )
    credit_account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="credit_entries",
    )
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LedgerEntryManager()

    class Meta:
        base_manager_name = "objects"
        default_manager_name = "objects"
        constraints = [
            models.CheckConstraint(check=Q(amount__gt=0), name="ledger_amount_gt_zero"),
            models.CheckConstraint(
                check=~Q(debit_account=F("credit_account")),
                name="ledger_debit_account_ne_credit_account",
            ),
        ]
        indexes = [
            models.Index(fields=["debit_account", "currency"]),
            models.Index(fields=["credit_account", "currency"]),
        ]

    def save(self, *args, **kwargs):
        legacy_via_service = kwargs.pop("_via_service", None)
        if legacy_via_service is not None:
            raise RuntimeError("LedgerEntry must be created via LedgerService")

        service_token = kwargs.pop("_service_token", None)
        if service_token is not _LEDGER_ENTRY_SERVICE_TOKEN:
            raise RuntimeError("LedgerEntry must be created via LedgerService")
        if not self._state.adding:
            raise RuntimeError("LedgerEntry is immutable")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("LedgerEntry is immutable")
