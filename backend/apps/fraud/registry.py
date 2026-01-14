"""
Registry initialization for fraud detection rules.
This module registers all active rules with the RuleRegistry.
"""
from apps.fraud.rules import RuleRegistry
from apps.fraud.rule_implementations import (
    DailyAmountLimitRule,
    TransactionFrequencyRule,
    RepeatedRecipientRule,
    RepeatedAmountPatternRule
)


def register_rules():
    """Register all active fraud detection rules"""
    # Clear existing rules (mainly for testing)
    RuleRegistry.clear()
    
    # Register rules in order of priority
    RuleRegistry.register(DailyAmountLimitRule())
    RuleRegistry.register(TransactionFrequencyRule())
    RuleRegistry.register(RepeatedRecipientRule())
    RuleRegistry.register(RepeatedAmountPatternRule())


# Register rules when this module is imported
register_rules()
