from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from apps.fraud.models import FraudEvent


@admin.register(FraudEvent)
class FraudEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'rule_code', 'risk_level', 'decision', 'transaction_link', 'created_at')
    list_filter = ('rule_code', 'risk_level', 'decision', 'created_at')
    search_fields = ('rule_code', 'transaction__idempotency_key')
    readonly_fields = ('transaction', 'rule_code', 'risk_level', 'decision', 'metadata', 'created_at')
    
    def transaction_link(self, obj):
        """Create a link to the related transaction in admin"""
        url = reverse('admin:transactions_transaction_change', args=[obj.transaction.id])
        return format_html('<a href="{}">{}</a>', url, obj.transaction.idempotency_key)
    
    transaction_link.short_description = 'Transaction'
    
    def has_add_permission(self, request):
        """Disable adding fraud events manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing fraud events"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting fraud events"""
        return False
