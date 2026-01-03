from django.db import models


class Account(models.Model):
    currency = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["currency"]),
        ]
