from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

# --- CORE PROJECT MODELS ---

class Category(models.Model):
    CATEGORY_TYPES = [('income', 'Income'), ('expense', 'Expense')]
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ['name', 'user']
    
    def __str__(self):
        return f"{self.name} ({self.category_type})"

class PaymentMode(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = [('income', 'Income'), ('expense', 'Expense')]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    payment_mode = models.ForeignKey(PaymentMode, on_delete=models.SET_NULL, null=True)
    
    # --- FIX: ADDED DESCRIPTION BACK ---
    description = models.TextField(blank=True, null=True) 
    
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']

class Receivable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    party_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    is_received = models.BooleanField(default=False)
    
    # --- ADD THESE TWO FIELDS BACK ---
    received_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    # ---------------------------------

    def __str__(self):
        return f"Receivable from {self.party_name} - {self.amount}"

class Payable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    party_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    # Add these just in case:
    paid_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20)
    message = models.TextField()
    severity = models.CharField(max_length=20, null=True, blank=True) 
    is_read = models.BooleanField(default=False) # Added to match screenshot
    created_at = models.DateTimeField(auto_now_add=True)
   
   

class Settings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    forecast_duration = models.CharField(max_length=100)
    alert_threshold_amount = models.DecimalField(decimal_places=2, max_digits=12)

class AlertSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    income_alert_enabled = models.BooleanField(default=True)
    expense_alert_enabled = models.BooleanField(default=True)

# ---------------------------------------------------------
# TRAINING MODELS (DYNAMIC)
# ---------------------------------------------------------

class IncomeTrainingData(models.Model):
    month_key = models.CharField(max_length=50)
    total_income = models.DecimalField(max_digits=15, decimal_places=2)
    growth = models.FloatField(default=1.0)

    class Meta:
        db_table = 'income_training_data'
        managed = False  # Let trainer.py handle the 1200 columns

class ExpenseTrainingData(models.Model):
    month_key = models.CharField(max_length=50)
    total_expense = models.DecimalField(max_digits=15, decimal_places=2)
    growth = models.FloatField(default=1.0)

    class Meta:
        db_table = 'expense_training_data'
        managed = False  # Let trainer.py handle the 1200 columns

