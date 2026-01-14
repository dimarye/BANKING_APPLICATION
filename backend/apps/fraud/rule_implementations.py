from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.db.models import Sum, Count
from django.utils import timezone

from apps.accounts.models import BankAccount
from apps.fraud.models import RiskLevel, Decision
from apps.fraud.rules import RiskRule, RuleResult
from apps.transactions.models import Transaction


class DailyAmountLimitRule(RiskRule):
    """Rule that checks if the total amount of transactions for an account exceeds a daily limit"""
    code = "DAILY_AMOUNT_LIMIT"
    risk_level = RiskLevel.HIGH
    
    # Configurable thresholds by account type
    THRESHOLDS = {
        BankAccount.ACCOUNT_TYPE_RETAIL: Decimal("10000.00"),
        BankAccount.ACCOUNT_TYPE_BUSINESS: Decimal("50000.00"),
    }
    
    def evaluate(self, transaction: Transaction) -> RuleResult:
        # Get the account type
        account_type = transaction.from_account.account_type
        
        # Get the threshold for this account type (default to retail if unknown)
        threshold = self.THRESHOLDS.get(account_type, self.THRESHOLDS[BankAccount.ACCOUNT_TYPE_RETAIL])
        
        # Calculate the time window (last 24 hours)
        time_window = timezone.now() - timedelta(days=1)
        
        # Get all completed transactions from this account in the last 24 hours
        completed_txs = Transaction.objects.filter(
            from_account=transaction.from_account,
            status=Transaction.STATUS_COMPLETED,
            created_at__gte=time_window
        )
        
        # Sum the amounts (excluding the current transaction)
        total_amount = completed_txs.aggregate(total=Sum('amount'))['total'] or Decimal("0")
        
        # Add the current transaction amount
        new_total = total_amount + transaction.amount
        
        # Check if the threshold is exceeded
        if new_total > threshold:
            return RuleResult(
                decision=Decision.BLOCK,
                reason=f"Daily transaction limit of {threshold} exceeded",
                metadata={
                    "threshold": str(threshold),
                    "total_amount": str(total_amount),
                    "new_total": str(new_total),
                    "account_type": account_type,
                }
            )
        elif new_total > threshold * Decimal("0.8"):
            # If we're at 80% of the threshold, flag but allow
            return RuleResult(
                decision=Decision.FLAG,
                reason=f"Daily transaction amount approaching limit ({new_total}/{threshold})",
                metadata={
                    "threshold": str(threshold),
                    "total_amount": str(total_amount),
                    "new_total": str(new_total),
                    "account_type": account_type,
                }
            )
        
        return RuleResult(
            decision=Decision.ALLOW,
            reason="Within daily transaction limit"
        )


class TransactionFrequencyRule(RiskRule):
    """Rule that checks if there are too many transactions in a short time period"""
    code = "TX_FREQUENCY_LIMIT"
    risk_level = RiskLevel.MEDIUM
    
    # Configuration: max transactions in time window (minutes)
    MAX_TX_COUNT = 5
    TIME_WINDOW_MINUTES = 10
    
    def evaluate(self, transaction: Transaction) -> RuleResult:
        # Calculate the time window
        time_window = timezone.now() - timedelta(minutes=self.TIME_WINDOW_MINUTES)
        
        # Count transactions from this account in the time window
        tx_count = Transaction.objects.filter(
            from_account=transaction.from_account,
            created_at__gte=time_window
        ).count()
        
        # Check if the frequency is too high
        if tx_count >= self.MAX_TX_COUNT:
            return RuleResult(
                decision=Decision.BLOCK,
                reason=f"Too many transactions ({tx_count}) in {self.TIME_WINDOW_MINUTES} minutes",
                metadata={
                    "max_count": self.MAX_TX_COUNT,
                    "time_window_minutes": self.TIME_WINDOW_MINUTES,
                    "actual_count": tx_count
                }
            )
        elif tx_count >= self.MAX_TX_COUNT - 1:
            # If we're close to the limit, flag but allow
            return RuleResult(
                decision=Decision.FLAG,
                reason=f"High transaction frequency ({tx_count}/{self.MAX_TX_COUNT} in {self.TIME_WINDOW_MINUTES} minutes)",
                metadata={
                    "max_count": self.MAX_TX_COUNT,
                    "time_window_minutes": self.TIME_WINDOW_MINUTES,
                    "actual_count": tx_count
                }
            )
        
        return RuleResult(
            decision=Decision.ALLOW,
            reason="Transaction frequency within normal limits"
        )


class RepeatedRecipientRule(RiskRule):
    """Rule that checks for multiple transfers to the same recipient in a short time"""
    code = "REPEATED_RECIPIENT"
    risk_level = RiskLevel.MEDIUM
    
    # Configuration
    MAX_TRANSFERS = 3
    TIME_WINDOW_HOURS = 2
    
    def evaluate(self, transaction: Transaction) -> RuleResult:
        # Calculate the time window
        time_window = timezone.now() - timedelta(hours=self.TIME_WINDOW_HOURS)
        
        # Count transactions to the same recipient in the time window
        recipient_count = Transaction.objects.filter(
            from_account=transaction.from_account,
            to_account=transaction.to_account,
            created_at__gte=time_window
        ).count()
        
        # Check if there are too many transfers to the same recipient
        if recipient_count >= self.MAX_TRANSFERS:
            return RuleResult(
                decision=Decision.FLAG,
                reason=f"Multiple transfers ({recipient_count}) to the same recipient in {self.TIME_WINDOW_HOURS} hours",
                metadata={
                    "max_transfers": self.MAX_TRANSFERS,
                    "time_window_hours": self.TIME_WINDOW_HOURS,
                    "actual_count": recipient_count,
                    "recipient_id": transaction.to_account.id
                }
            )
        
        return RuleResult(
            decision=Decision.ALLOW,
            reason="Normal recipient pattern"
        )


class RepeatedAmountPatternRule(RiskRule):
    """Rule that checks for repeated transfers of the same amount"""
    code = "REPEATED_AMOUNT_PATTERN"
    risk_level = RiskLevel.LOW
    
    # Configuration
    MAX_SAME_AMOUNT = 3
    TIME_WINDOW_HOURS = 24
    
    def evaluate(self, transaction: Transaction) -> RuleResult:
        # Calculate the time window
        time_window = timezone.now() - timedelta(hours=self.TIME_WINDOW_HOURS)
        
        # Count transactions with the same amount in the time window
        same_amount_count = Transaction.objects.filter(
            from_account=transaction.from_account,
            amount=transaction.amount,
            created_at__gte=time_window
        ).count()
        
        # Check if there are too many transfers of the same amount
        if same_amount_count >= self.MAX_SAME_AMOUNT:
            return RuleResult(
                decision=Decision.FLAG,
                reason=f"Multiple transfers ({same_amount_count}) of the same amount ({transaction.amount}) in {self.TIME_WINDOW_HOURS} hours",
                metadata={
                    "max_same_amount": self.MAX_SAME_AMOUNT,
                    "time_window_hours": self.TIME_WINDOW_HOURS,
                    "actual_count": same_amount_count,
                    "amount": str(transaction.amount)
                }
            )
        
        return RuleResult(
            decision=Decision.ALLOW,
            reason="Normal amount pattern"
        )
