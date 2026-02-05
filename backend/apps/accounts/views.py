from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from django.db import transaction
from .models import BankAccount
from .serializers import (
    UserRegistrationSerializer, UserSerializer, 
    BankAccountSerializer, BankAccountCreateSerializer,
    TransactionSerializer, DepositSerializer, WithdrawalSerializer
)
from .services import AccountService
from apps.core.exceptions import (
    InsufficientFundsError, AccountNotFoundError, 
    AccountFrozenError
)
from apps.transactions.services import TransactionService
from .auth import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view with rate limiting"""
    serializer_class = CustomTokenObtainPairSerializer
    
    @ratelimit(key='ip', rate='5/m', block=True)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    @ratelimit(key='ip', rate='3/m', block=True)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class BankAccountListView(generics.ListCreateAPIView):
    """List and create bank accounts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BankAccountCreateSerializer
        return BankAccountSerializer
    
    @ratelimit(key='user', rate='10/h', block=True)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BankAccountDetailView(generics.RetrieveAPIView):
    """Get bank account details"""
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='30/h', block=True)
def transfer_money(request):
    """Transfer money between accounts"""
    serializer = TransactionSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                tx = TransactionService.process_transfer(
                    idempotency_key=request.data.get('idempotency_key'),
                    from_account_id=serializer.validated_data['from_account_id'],
                    to_account_id=serializer.validated_data['to_account_id'],
                    amount=serializer.validated_data['amount'],
                    currency=serializer.validated_data['currency'],
                    description=serializer.validated_data.get('description', '')
                )
                
                # Serialize the created transaction
                from apps.transactions.serializers import TransactionSerializer
                tx_serializer = TransactionSerializer(tx)
                
                return Response(tx_serializer.data, status=status.HTTP_201_CREATED)
                
        except InsufficientFundsError as e:
            return Response(
                {"error": "INSUFFICIENT_FUNDS", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except AccountFrozenError as e:
            return Response(
                {"error": "ACCOUNT_FROZEN", "message": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"error": "TRANSFER_FAILED", "message": "Transfer failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='20/h', block=True)
def deposit_money(request):
    """Deposit money to account"""
    serializer = DepositSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                AccountService.deposit(
                    account_id=serializer.validated_data['account'].id,
                    amount=serializer.validated_data['amount'],
                    description=serializer.validated_data.get('description', 'Deposit')
                )
                
                # Get updated account data
                account = BankAccount.objects.get(id=serializer.validated_data['account'].id)
                account_serializer = BankAccountSerializer(account)
                
                return Response(account_serializer.data, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {"error": "DEPOSIT_FAILED", "message": "Deposit failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='20/h', block=True)
def withdraw_money(request):
    """Withdraw money from account"""
    serializer = WithdrawalSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                AccountService.withdraw(
                    account_id=serializer.validated_data['account'].id,
                    amount=serializer.validated_data['amount'],
                    description=serializer.validated_data.get('description', 'Withdrawal')
                )
                
                # Get updated account data
                account = BankAccount.objects.get(id=serializer.validated_data['account'].id)
                account_serializer = BankAccountSerializer(account)
                
                return Response(account_serializer.data, status=status.HTTP_200_OK)
                
        except InsufficientFundsError as e:
            return Response(
                {"error": "INSUFFICIENT_FUNDS", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except AccountFrozenError as e:
            return Response(
                {"error": "ACCOUNT_FROZEN", "message": str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"error": "WITHDRAWAL_FAILED", "message": "Withdrawal failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
