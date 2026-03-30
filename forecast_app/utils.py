from .models import Category, PaymentMode

def create_default_categories(user):
    income_categories = [
        'Salary', 'Freelance', 'Business Income', 'Investment Returns',
        'Rental Income', 'Bonus', 'Interest', 'Other Income'
    ]

    for cat_name in income_categories:
        Category.objects.get_or_create(
            name=cat_name,
            category_type='income',
            user=user
        )

    expense_categories = [
        'Entertainment', 'Rent', 'Groceries', 'Utilities', 'Transportation',
        'Healthcare', 'Education', 'Insurance', 'Shopping', 'Dining Out',
        'Travel', 'Savings', 'Investment', 'EMI', 'Mobile/Internet',
        'Clothing', 'Personal Care', 'Gifts', 'Subscriptions', 'Other Expenses'
    ]

    for cat_name in expense_categories:
        Category.objects.get_or_create(
            name=cat_name,
            category_type='expense',
            user=user
        )


def create_default_payment_modes(user):
    payment_modes = [
        'Cash', 'Bank Transfer', 'UPI', 'Credit Card',
        'Debit Card', 'Cheque', 'Digital Wallet', 'Net Banking'
    ]

    for mode_name in payment_modes:
        PaymentMode.objects.get_or_create(
            name=mode_name,
            user=user
        )

from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from .models import Transaction


# ===============================
# CURRENT BALANCE
# ===============================
def calculate_current_balance(user):
    income = Transaction.objects.filter(
        user=user,
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    expense = Transaction.objects.filter(
        user=user,
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    return income - expense


# ===============================
# PERCENTAGE CHANGE
# ===============================
def calculate_percentage_change(previous, current):
    if previous == 0:
        return 0
    return round(((current - previous) / previous) * 100, 2)


# ===============================
# FORECAST CHART (NEXT 6 MONTHS)
# ===============================
def get_forecast_chart_data(user):
    today = timezone.now().date()
    data = []

    for i in range(6):
        month_start = (today.replace(day=1) + timedelta(days=32*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        income = Transaction.objects.filter(
            user=user,
            transaction_type='income',
            date__range=(month_start, month_end)
        ).aggregate(total=Sum('amount'))['total'] or 0

        expense = Transaction.objects.filter(
            user=user,
            transaction_type='expense',
            date__range=(month_start, month_end)
        ).aggregate(total=Sum('amount'))['total'] or 0

        data.append({
            "month": month_start.strftime("%b %Y"),
            "income": float(income),
            "expense": float(expense),
        })

    return data
