from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Type

from apps.fraud.models import RiskLevel, Decision
from apps.transactions.models import Transaction


@dataclass
class RuleResult:
    """Result of a risk rule evaluation"""
    decision: Decision
    reason: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RiskRule(ABC):
    """Base class for all risk rules"""
    code: str
    risk_level: RiskLevel
    
    @abstractmethod
    def evaluate(self, transaction: Transaction) -> RuleResult:
        """
        Evaluate the rule against a transaction
        
        Args:
            transaction: The transaction to evaluate
            
        Returns:
            RuleResult with decision, reason and optional metadata
        """
        pass


class RuleRegistry:
    """Registry of all active risk rules"""
    _rules: List[RiskRule] = []
    
    @classmethod
    def register(cls, rule: RiskRule) -> None:
        """
        Register a rule with the registry
        
        Args:
            rule: The rule to register
        """
        cls._rules.append(rule)
        # Sort rules by risk level (highest first) to ensure critical rules run first
        cls._rules.sort(key=lambda r: {
            RiskLevel.CRITICAL: 0,
            RiskLevel.HIGH: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 3
        }.get(r.risk_level, 4))
    
    @classmethod
    def get_rules(cls) -> List[RiskRule]:
        """
        Get all registered rules
        
        Returns:
            List of registered rules
        """
        return cls._rules.copy()
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered rules (mainly for testing)"""
        cls._rules = []


class RuleEngine:
    """Engine for evaluating risk rules against transactions"""
    
    @classmethod
    def evaluate_transaction(cls, transaction: Transaction) -> List[RuleResult]:
        """
        Evaluate all registered rules against a transaction
        
        Args:
            transaction: The transaction to evaluate
            
        Returns:
            List of rule results
        """
        results = []
        
        for rule in RuleRegistry.get_rules():
            result = rule.evaluate(transaction)
            if result.decision != Decision.ALLOW:
                results.append((rule, result))
                
                # If any rule decides to BLOCK, we can short-circuit
                if result.decision == Decision.BLOCK:
                    break
                    
        return results
