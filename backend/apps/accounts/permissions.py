from rest_framework import permissions
from .models import BankAccount


class IsAccountOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an account to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user
        
        # Write permissions are only allowed to the owner of the account
        return obj.user == request.user


class IsTransactionParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants of a transaction to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user is owner of either source or destination account
        user_accounts = request.user.bank_accounts.all()
        return (obj.from_account in user_accounts or 
                obj.to_account in user_accounts)


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_staff
