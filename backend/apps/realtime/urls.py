from django.urls import path
from . import views

app_name = 'realtime'

urlpatterns = [
    # API endpoints for real-time features
    path('ws-info/', views.websocket_info, name='websocket_info'),
    path('test-notification/', views.test_notification, name='test_notification'),
]
