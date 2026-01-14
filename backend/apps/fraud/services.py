from typing import List, Tuple, Optional

from django.db import transaction

from apps.fraud.models import FraudEvent, Decision, RiskLevel
from apps.fraud.rules import RiskRule, RuleResult, RuleEngine
from apps.transactions.models import Transaction


class FraudDetectionError(Exception):
    """Exception raised when a transaction is blocked by fraud detection"""
    def __init__(self, rule_code: str, reason: str):
        self.rule_code = rule_code
        self.reason = reason
        super().__init__(f"Transaction blocked by fraud detection: {rule_code} - {reason}")


class FraudService:
    """Service for fraud detection and management"""
    
    @staticmethod
    def evaluate_transaction(tx: Transaction) -> List[FraudEvent]:
        """
        Evaluate a transaction against all fraud rules
        
        Args:
            tx: The transaction to evaluate
            
        Returns:
            List of created FraudEvent objects
            
        Raises:
            FraudDetectionError: If any rule blocks the transaction
        """
        # Evaluate all rules against the transaction
        rule_results = RuleEngine.evaluate_transaction(tx)
        fraud_events = []
        
        # Process results and create FraudEvent records
        with transaction.atomic():
            for rule, result in rule_results:
                # Create a FraudEvent for each FLAG or BLOCK decision
                if result.decision in [Decision.FLAG, Decision.BLOCK]:
                    event = FraudEvent.objects.create(
                        transaction=tx,
                        rule_code=rule.code,
                        risk_level=rule.risk_level,
                        decision=result.decision,
                        metadata={
                            "reason": result.reason,
                            **(result.metadata or {})
                        }
                    )
                    fraud_events.append(event)
            
            # After creating all events, check if any rule blocked the transaction
            for rule, result in rule_results:
                if result.decision == Decision.BLOCK:
                    raise FraudDetectionError(rule.code, result.reason)
        
        return fraud_events
    
    @staticmethod
    def get_fraud_events_for_transaction(tx: Transaction) -> List[FraudEvent]:
        """
        Get all fraud events for a transaction
        
        Args:
            tx: The transaction to get events for
            
        Returns:
            List of FraudEvent objects
        """
        return FraudEvent.objects.filter(transaction=tx).order_by('-risk_level', 'created_at')
    
    @staticmethod
    def has_blocking_events(tx: Transaction) -> bool:
        """
        Check if a transaction has any blocking fraud events
        
        Args:
            tx: The transaction to check
            
        Returns:
            True if the transaction has any blocking events, False otherwise
        """
        return FraudEvent.objects.filter(
            transaction=tx,
            decision=Decision.BLOCK
        ).exists()
