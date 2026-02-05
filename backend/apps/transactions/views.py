from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit
from django.db import models
from .models import Transaction
from .serializers import TransactionSerializer, TransactionCreateSerializer


class TransactionListView(generics.ListAPIView):
    """List user's transactions"""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Get transactions where user is either sender or receiver
        user_accounts = self.request.user.bank_accounts.all()
        return Transaction.objects.filter(
            models.Q(from_account__in=user_accounts) | 
            models.Q(to_account__in=user_accounts)
        ).order_by('-created_at')


class TransactionDetailView(generics.RetrieveAPIView):
    """Get transaction details"""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_accounts = self.request.user.bank_accounts.all()
        return Transaction.objects.filter(
            models.Q(from_account__in=user_accounts) | 
            models.Q(to_account__in=user_accounts)
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='30/h', block=True)
def create_transaction(request):
    """Create a new transaction"""
    serializer = TransactionCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            transaction = serializer.save()
            response_serializer = TransactionSerializer(transaction)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": "TRANSACTION_FAILED", "message": "Transaction failed. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
