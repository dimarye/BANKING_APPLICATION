from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BankAccount
from apps.ledger.services import get_account_balance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=100)
    
    class Meta:
        model = User
        fields = ('email', 'full_name', 'password', 'password_confirm')
    
    def validate_email(self, value):
        """Validate that email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('full_name', ''),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    full_name = serializers.CharField(source='first_name', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for bank account"""
    balance = serializers.SerializerMethodField()
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = BankAccount
        fields = (
            'id', 'account_number', 'account_type', 'currency', 
            'status', 'balance', 'overdraft_limit', 'created_at', 
            'updated_at', 'owner'
        )
        read_only_fields = (
            'id', 'account_number', 'created_at', 'updated_at', 'owner'
        )
    
    def get_balance(self, obj):
        """Get current balance for the account"""
        try:
            return get_account_balance(obj.ledger_account, obj.currency)
        except Exception:
            return None
    
    def validate_account_type(self, value):
        """Validate account type"""
        valid_types = [choice[0] for choice in BankAccount.ACCOUNT_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid account type. Must be one of: {valid_types}")
        return value
    
    def validate_currency(self, value):
        """Validate currency code"""
        if len(value) != 3:
            raise serializers.ValidationError("Currency must be a 3-letter ISO code.")
        return value.upper()


class BankAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bank accounts"""
    overdraft_limit = serializers.DecimalField(
        max_digits=18, 
        decimal_places=4, 
        default=0, 
        min_value=0
    )
    
    class Meta:
        model = BankAccount
        fields = (
            'account_type', 'currency', 'overdraft_limit'
        )
    
    def validate_currency(self, value):
        """Validate currency code"""
        if len(value) != 3:
            raise serializers.ValidationError("Currency must be a 3-letter ISO code.")
        return value.upper()
    
    def create(self, validated_data):
        """Create bank account for authenticated user"""
        from apps.ledger.models import Account
        from django.db import transaction
        
        user = self.context['request'].user
        
        with transaction.atomic():
            # Create ledger account first
            ledger_account = Account.objects.create(currency=validated_data['currency'])
            
            # Create bank account
            bank_account = BankAccount.objects.create(
                user=user,
                ledger_account=ledger_account,
                **validated_data
            )
            
        return bank_account


class TransactionSerializer(serializers.Serializer):
    """Serializer for money transfer operations"""
    from_account_id = serializers.IntegerField()
    to_account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=0.01)
    currency = serializers.CharField(max_length=3)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
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
            from_account = BankAccount.objects.get(
                id=attrs['from_account_id'], 
                user=user
            )
            to_account = BankAccount.objects.get(id=attrs['to_account_id'])
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError("Invalid account ID or account not found.")
        
        # Check if accounts are active
        if from_account.status != BankAccount.STATUS_ACTIVE:
            raise serializers.ValidationError("Source account is not active.")
        
        if to_account.status != BankAccount.STATUS_ACTIVE:
            raise serializers.ValidationError("Destination account is not active.")
        
        # Check currency match
        if (from_account.currency != attrs['currency'] or 
            to_account.currency != attrs['currency']):
            raise serializers.ValidationError("Currency mismatch between accounts.")
        
        # Check sufficient funds
        from apps.ledger.services import get_account_balance
        balance = get_account_balance(from_account.ledger_account, from_account.currency)
        if balance + from_account.overdraft_limit < attrs['amount']:
            raise serializers.ValidationError("Insufficient funds.")
        
        attrs['from_account'] = from_account
        attrs['to_account'] = to_account
        
        return attrs


class DepositSerializer(serializers.Serializer):
    """Serializer for deposit operations"""
    account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate deposit data"""
        user = self.context['request'].user
        
        try:
            account = BankAccount.objects.get(
                id=attrs['account_id'], 
                user=user
            )
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError("Invalid account ID or account not found.")
        
        if account.status != BankAccount.STATUS_ACTIVE:
            raise serializers.ValidationError("Account is not active.")
        
        attrs['account'] = account
        return attrs


class WithdrawalSerializer(serializers.Serializer):
    """Serializer for withdrawal operations"""
    account_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate withdrawal data"""
        user = self.context['request'].user
        
        try:
            account = BankAccount.objects.get(
                id=attrs['account_id'], 
                user=user
            )
        except BankAccount.DoesNotExist:
            raise serializers.ValidationError("Invalid account ID or account not found.")
        
        if account.status != BankAccount.STATUS_ACTIVE:
            raise serializers.ValidationError("Account is not active.")
        
        # Check sufficient funds
        from apps.ledger.services import get_account_balance
        balance = get_account_balance(account.ledger_account, account.currency)
        if balance + account.overdraft_limit < attrs['amount']:
            raise serializers.ValidationError("Insufficient funds.")
        
        attrs['account'] = account
        return attrs
