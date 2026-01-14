from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.transactions.models import Transaction


class RiskLevel(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class Decision(models.TextChoices):
    ALLOW = "ALLOW", _("Allow")
    FLAG = "FLAG", _("Flag")
    BLOCK = "BLOCK", _("Block")


class FraudEvent(models.Model):
    """
    Records fraud detection events for transactions.
    Each rule evaluation that results in FLAG or BLOCK creates one FraudEvent.
    """
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name="fraud_events"
    )
    rule_code = models.CharField(max_length=100)
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW
    )
    decision = models.CharField(
        max_length=10,
        choices=Decision.choices
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["transaction", "rule_code"],
                name="unique_rule_per_transaction"
            ),
        ]
        indexes = [
            models.Index(fields=["rule_code"]),
            models.Index(fields=["risk_level"]),
            models.Index(fields=["decision"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.rule_code} - {self.decision} ({self.risk_level})"
