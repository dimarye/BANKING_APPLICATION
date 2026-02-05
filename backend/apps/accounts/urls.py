from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    
    # Bank Accounts
    path('accounts/', views.BankAccountListView.as_view(), name='account-list'),
    path('accounts/<int:pk>/', views.BankAccountDetailView.as_view(), name='account-detail'),
    
    # Operations
    path('operations/transfer/', views.transfer_money, name='transfer'),
    path('operations/deposit/', views.deposit_money, name='deposit'),
    path('operations/withdraw/', views.withdraw_money, name='withdraw'),
]
