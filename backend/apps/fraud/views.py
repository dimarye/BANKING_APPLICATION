from rest_framework import generics, permissions
from django_ratelimit.decorators import ratelimit
from .models import FraudEvent
from .serializers import FraudEventSerializer


class FraudEventListView(generics.ListAPIView):
    """List fraud events for user's transactions"""
    serializer_class = FraudEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Get fraud events for user's transactions
        user_accounts = self.request.user.bank_accounts.all()
        from django.db import models
        from apps.transactions.models import Transaction
        
        user_transactions = Transaction.objects.filter(
            models.Q(from_account__in=user_accounts) | 
            models.Q(to_account__in=user_accounts)
        )
        
        return FraudEvent.objects.filter(transaction__in=user_transactions).order_by('-created_at')
    
    @ratelimit(key='user', rate='100/h', block=True)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class FraudEventDetailView(generics.RetrieveAPIView):
    """Get fraud event details"""
    serializer_class = FraudEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_accounts = self.request.user.bank_accounts.all()
        from django.db import models
        from apps.transactions.models import Transaction
        
        user_transactions = Transaction.objects.filter(
            models.Q(from_account__in=user_accounts) | 
            models.Q(to_account__in=user_accounts)
        )
        
        return FraudEvent.objects.filter(transaction__in=user_transactions)
