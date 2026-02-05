from django.urls import path
from . import views

app_name = 'fraud'

urlpatterns = [
    path('events/', views.FraudEventListView.as_view(), name='fraud-event-list'),
    path('events/<uuid:pk>/', views.FraudEventDetailView.as_view(), name='fraud-event-detail'),
]
