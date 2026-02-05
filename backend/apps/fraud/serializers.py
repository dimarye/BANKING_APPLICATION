from rest_framework import serializers
from .models import FraudEvent


class FraudEventSerializer(serializers.ModelSerializer):
    """Serializer for fraud events"""
    transaction_id = serializers.UUIDField(source='transaction.id', read_only=True)
    
    class Meta:
        model = FraudEvent
        fields = (
            'id', 'transaction_id', 'rule_code', 'risk_level', 
            'decision', 'metadata', 'created_at'
        )
        read_only_fields = (
            'id', 'transaction_id', 'rule_code', 'risk_level', 
            'decision', 'metadata', 'created_at'
        )
