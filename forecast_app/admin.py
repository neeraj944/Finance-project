# Register your models here.
from django.contrib import admin
from .models import (
    Category, PaymentMode, Transaction, Receivable, 
    Payable, Alert, Settings
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'user', 'created_at']
    list_filter = ['category_type', 'created_at']
    search_fields = ['name', 'user__username']

@admin.register(PaymentMode)
class PaymentModeAdmin(admin.ModelAdmin):
    list_display = ['name', 'user']
    search_fields = ['name', 'user__username']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'category', 'date', 'created_at']
    list_filter = ['transaction_type', 'date', 'category']
    # If you added 'description' back to the model, keep it here. 
    # If not, remove it from search_fields.
    search_fields = ['user__username', 'description']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']

@admin.register(Receivable)
class ReceivableAdmin(admin.ModelAdmin):
    list_display = ['party_name', 'amount', 'due_date', 'is_received', 'user']
    list_filter = ['is_received']
    search_fields = ['party_name', 'description']
    date_hierarchy = 'due_date'

@admin.register(Payable)
class PayableAdmin(admin.ModelAdmin):
    list_display = ['party_name', 'amount', 'due_date', 'is_paid', 'user']
    list_filter = ['is_paid']
    search_fields = ['party_name', 'description']
    date_hierarchy = 'due_date'

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    # FIXED: Removed 'severity' and 'is_read' because they are not in your model
    list_display = ['user', 'alert_type', 'created_at']
    list_filter = ['alert_type', 'created_at']
    search_fields = ['message', 'user__username']

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'forecast_duration', 'alert_threshold_amount']