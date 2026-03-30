from django import forms
from django.forms import ModelForm
from .models import Transaction, Category, PaymentMode, Receivable, Payable, Settings
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
TAILWIND_INPUT = (
    "mt-1 block w-full rounded-lg "
    "border border-gray-300 px-3 py-2 "
    "focus:border-green-600 focus:ring-2 "
    "focus:ring-green-200 outline-none"
)


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'category', 'payment_mode', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
        }

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'payment_mode', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(
                user=user, category_type='income'
            )
            self.fields['payment_mode'].queryset = PaymentMode.objects.filter(user=user)

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'payment_mode', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(
                user=user, category_type='expense'
            )
            self.fields['payment_mode'].queryset = PaymentMode.objects.filter(user=user)

class ReceivableForm(forms.ModelForm):
    class Meta:
        model = Receivable
        fields = ['party_name', 'amount', 'due_date', 'description','is_received','received_date']
        widgets = {
            'party_name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT
            }),
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'class': TAILWIND_INPUT
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': TAILWIND_INPUT
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': TAILWIND_INPUT
            }),
            'is_received': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-green-600 rounded'
            }),
            'received_date': forms.DateInput(attrs={
                'type': 'date',
                'class': TAILWIND_INPUT
            }),
        }

class PayableForm(forms.ModelForm):
    class Meta:
        model = Payable
        fields = ['party_name', 'amount', 'due_date', 'description','is_paid','paid_date']
        widgets = {
            'party_name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT
            }),
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'class': TAILWIND_INPUT
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': TAILWIND_INPUT
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': TAILWIND_INPUT
            }),
            'is_paid': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-green-600 rounded'
            }),
            'paid_date': forms.DateInput(attrs={
                'type': 'date',
                'class': TAILWIND_INPUT
            }),
        }


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:outline-none"
            })

# class Incomeform(forms.ModelForm):
#     class Meta:
#         model = Income
#         fields = "__all__"
#         widgets = {
#             'amount': forms.NumberInput(attrs={
#                 'class': 'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-300'
#             }),
#             'date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-300'
#             }),
#             'payment_mode': forms.Select(attrs={
#                 'class': 'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:border-green-500 focus:ring-2 focus:ring-green-300'
#             }),
#             'description': forms.Textarea(attrs={
#                 'rows': 3,
#                 'class': 'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-300'
#             }),
#         }

# class Categorysform(ModelForm):
#     class Meta:
#         model=Categorys
#         fields=['category_name','category_type']

# class Expenseform(ModelForm):
#     class Meta:
#         model = Expense
#         fields = ['amount', 'date', 'payment_mode', 'description']
#         widgets = {
#             'amount': forms.NumberInput(attrs={
#                 'class': 'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-300'
#             }),
#             'date': forms.DateInput(attrs={
#                 'type': 'date',
#                 'class': 'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-300'
#             }),
#             'payment_mode': forms.Select(attrs={
#                 'class': 'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:border-green-500 focus:ring-2 focus:ring-green-300'
#             }),
#             'description': forms.Textarea(attrs={
#                 'rows': 3,
#                 'class': 'mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:ring-2 focus:ring-green-300'
#             }),
#         }

from django.forms import ModelForm
from .models import Settings

class Settingsform(ModelForm):
    class Meta:
        model = Settings
        fields = ['forecast_duration', 'alert_threshold_amount']
        widgets = {
            'forecast_duration': forms.Select(attrs={
                'class': TAILWIND_INPUT
            }),
            'alert_threshold_amount': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT
            }),
        }
