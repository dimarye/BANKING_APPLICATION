from rest_framework import serializers
from .models import Transaction
from apps.accounts.serializers import BankAccountSerializer


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transaction data"""
    from_account = BankAccountSerializer(read_only=True)
    to_account = BankAccountSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = (
            'id', 'idempotency_key', 'from_account', 'to_account', 
            'amount', 'currency', 'status', 'description', 
            'created_at', 'updated_at', 'error_code', 'error_message'
        )
        read_only_fields = (
            'id', 'idempotency_key', 'status', 'created_at', 
            'updated_at', 'error_code', 'error_message'
        )


class TransactionCreateSerializer(serializers.Serializer):
    """Serializer for creating transactions"""
    from_account_id = serializers.IntegerField(write_only=True)
    to_account_id = serializers.IntegerField(write_only=True)
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=0.01)
    currency = serializers.CharField(max_length=3)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=255, required=False)
    
    def validate_currency(self, value):
        """Validate currency code"""
        if len(value) != 3:
            raise serializers.ValidationError("Currency must be a 3-letter ISO code.")
        return value.upper()
    
    def validate(self, attrs):
        """Validate transaction data"""
        if attrs['from_account_id'] == attrs['to_account_id']:
            raise serializers.ValidationError("Cannot transfer to the same account.")
        
        # Check if accounts exist and belong to user
        user = self.context['request'].user
        
        try:
            from apps.accounts.models import BankAccount
            from_account = BankAccount.objects.get(
                id=attrs['from_account_id'], 
                user=user
            )
            to_account = BankAccount.objects.get(id=attrs['to_account_id'])
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError("Invalid account ID or account not found.")
        
        # Check if accounts are active
        if from_account.status != from_account.STATUS_ACTIVE:
            raise serializers.ValidationError("Source account is not active.")
        
        if to_account.status != to_account.STATUS_ACTIVE:
            raise serializers.ValidationError("Destination account is not active.")
        
        # Check currency match
        if (from_account.currency != attrs['currency'] or 
            to_account.currency != attrs['currency']):
            raise serializers.ValidationError("Currency mismatch between accounts.")
        
        attrs['from_account'] = from_account
        attrs['to_account'] = to_account
        
        return attrs
    
    def create(self, validated_data):
        """Create transaction using TransactionService"""
        from .services import TransactionService
        
        return TransactionService.process_transfer(
            idempotency_key=validated_data.get('idempotency_key'),
            from_account_id=validated_data['from_account_id'],
            to_account_id=validated_data['to_account_id'],
            amount=validated_data['amount'],
            currency=validated_data['currency'],
            description=validated_data.get('description', '')
        )
