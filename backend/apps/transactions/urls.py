from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction-list'),
    path('<uuid:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path('create/', views.create_transaction, name='transaction-create'),
]
