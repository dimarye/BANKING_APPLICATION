from django.db import migrations, models
import django.db.models.deletion
from django.db.models import F, Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LedgerEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "debit_account",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="debit_entries", to="accounts.account"),
                ),
                (
                    "credit_account",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="credit_entries", to="accounts.account"),
                ),
                ("amount", models.DecimalField(decimal_places=4, max_digits=18)),
                ("currency", models.CharField(max_length=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="ledgerentry",
            constraint=models.CheckConstraint(check=Q(amount__gt=0), name="ledger_amount_gt_zero"),
        ),
        migrations.AddConstraint(
            model_name="ledgerentry",
            constraint=models.CheckConstraint(
                check=~Q(debit_account=F("credit_account")),
                name="ledger_debit_account_ne_credit_account",
            ),
        ),
        migrations.AddIndex(
            model_name="ledgerentry",
            index=models.Index(fields=["debit_account", "currency"], name="ledger_ledger_debit_currency_idx"),
        ),
        migrations.AddIndex(
            model_name="ledgerentry",
            index=models.Index(fields=["credit_account", "currency"], name="ledger_ledger_credit_currency_idx"),
        ),
    ]
