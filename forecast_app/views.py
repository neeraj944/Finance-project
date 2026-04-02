from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Transaction, Category, PaymentMode, Receivable, Payable, Alert, Settings, AlertSetting
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import authenticate, login
from .forms import RegisterForm, ReceivableForm, PayableForm, Settingsform
from .utils import calculate_current_balance

# --- ML ENGINE INTEGRATION ---
import subprocess
import os
from ml_engine.predictor import FinancePredictor


def _is_admin_user(user):
    return user.is_staff or user.is_superuser


def _scope_queryset_for_user(queryset, user):
    # Shared mode: every authenticated user can access the same finance dataset.
    return queryset


# ────────────────────────────────────────────────────────────
# DASHBOARD & API 
# ────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = timezone.now().date()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    current_balance = calculate_current_balance(request.user) or Decimal('0.00')
    first_day_month = today.replace(day=1)
    transaction_scope = _scope_queryset_for_user(Transaction.objects.all(), request.user)

    # Current Month Totals
    monthly_income = transaction_scope.filter(
        transaction_type='income', date__gte=first_day_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    monthly_expense = transaction_scope.filter(
        transaction_type='expense', date__gte=first_day_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    
    forecast = {
        'income': None,
        'expense': None,
        'net': None,
        'target_month': selected_month,
        'target_year': selected_year,
        'income_categories': {},
        'expense_categories': {},
        'ai_explanation': [],
    }

    context = {
        'current_balance': current_balance,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'monthly_net': monthly_income - monthly_expense,
        'forecast': forecast,
        'recent_transactions': transaction_scope.order_by('-date')[:10],
        'alerts': Alert.objects.filter(user=request.user).order_by('-created_at')[:5],
    }
    return render(request, 'forecast_app/dashboard.html', context)

@login_required
def run_trainer(request):
    """Triggers the trainer.py script to update all category .pkl files"""
    try:
        # Construct path to trainer.py
        script_path = os.path.join(os.path.dirname(__file__), 'ml_engine', 'trainer.py')
        subprocess.run(['python3', script_path], check=True)
        messages.success(request, "ML Models re-trained successfully with 7-digit trends!")
    except Exception as e:
        messages.error(request, f"Training failed: {e}")
    return redirect('dashboard')

def predict_cashflow_api(request):
    target_str = request.GET.get('target')

    if not target_str:
        return JsonResponse({'error': 'No date selected'}, status=400)

    try:
        dt = datetime.strptime(target_str, '%Y-%m')

        res = FinancePredictor().get_net_cash_flow(request.user.id, dt.year, dt.month)

        return JsonResponse({
            'income': res['total_income'],
            'expense': res['total_expense'],
            'net_cash': res['net_cash'],
            'income_categories': res.get('income_categories', {}),
            'expense_categories': res.get('expense_categories', {}),
            'ai_explanation': res['ai_explanation']   # IMPORTANT
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ────────────────────────────────────────────────────────────
# INCOME & EXPENSE CRUD
# ────────────────────────────────────────────────────────────

@login_required
def income_list(request):
    incomes = _scope_queryset_for_user(
        Transaction.objects.filter(transaction_type='income'),
        request.user
    ).order_by('-date')
    return render(request, 'forecast_app/income_list.html', {'incomes': incomes})

@login_required
def add_income(request):
    if request.method == 'POST':
        Transaction.objects.create(
            user=request.user, transaction_type='income', 
            amount=Decimal(request.POST.get('amount')),
            category_id=request.POST.get('category'), date=request.POST.get('date')
        )
        messages.success(request, "Income added. Run 'Train Models' to update forecast.")
        return redirect('income_list')
    categories = _scope_queryset_for_user(
        Category.objects.filter(category_type='income'),
        request.user
    ).order_by('name')
    return render(request, 'forecast_app/add_income.html', {'categories': categories})

@login_required
def edit_income(request, pk):
    income = get_object_or_404(
        _scope_queryset_for_user(Transaction.objects.filter(transaction_type='income'), request.user),
        pk=pk
    )
    categories = _scope_queryset_for_user(
        Category.objects.filter(category_type='income'),
        request.user
    ).order_by('name')
    payment_modes = _scope_queryset_for_user(
        PaymentMode.objects.all(),
        request.user
    ).order_by('name')

    if request.method == 'POST':
        category = Category.objects.filter(
            id=request.POST.get('category'),
            category_type='income'
        ).first()
        payment_mode = PaymentMode.objects.filter(id=request.POST.get('payment_mode')).first()

        if not category or not payment_mode:
            messages.error(request, "Please select a valid category and payment mode.")
        else:
            try:
                income.amount = Decimal(request.POST.get('amount'))
            except Exception:
                messages.error(request, "Please enter a valid amount.")
            else:
                income.category = category
                income.payment_mode = payment_mode
                income.date = request.POST.get('date') or income.date
                income.description = (request.POST.get('description') or '').strip()
                income.save()
                messages.success(request, "Income updated successfully.")
                return redirect('income_list')

    return render(request, 'forecast_app/edit_income.html', {
        'income': income,
        'categories': categories,
        'payment_modes': payment_modes,
    })

@login_required
def delete_income(request, pk):
    get_object_or_404(
        _scope_queryset_for_user(Transaction.objects.filter(transaction_type='income'), request.user),
        pk=pk
    ).delete()
    return redirect('income_list')

@login_required
def expense_list(request):
    expenses = _scope_queryset_for_user(
        Transaction.objects.filter(transaction_type='expense'),
        request.user
    ).order_by('-date')
    return render(request, 'forecast_app/expense_list.html', {'expenses': expenses})

@login_required
def add_expense(request):
    if request.method == 'POST':
        Transaction.objects.create(
            user=request.user, transaction_type='expense', 
            amount=Decimal(request.POST.get('amount')),
            category_id=request.POST.get('category'), date=request.POST.get('date')
        )
        return redirect('expense_list')
    categories = _scope_queryset_for_user(
        Category.objects.filter(category_type='expense'),
        request.user
    ).order_by('name')
    return render(request, 'forecast_app/add_expense.html', {'categories': categories})

@login_required
def edit_expense(request, pk):
    exp = get_object_or_404(
        _scope_queryset_for_user(Transaction.objects.filter(transaction_type='expense'), request.user),
        pk=pk
    )
    categories = _scope_queryset_for_user(
        Category.objects.filter(category_type='expense'),
        request.user
    ).order_by('name')
    payment_modes = _scope_queryset_for_user(
        PaymentMode.objects.all(),
        request.user
    ).order_by('name')

    if request.method == 'POST':
        category = Category.objects.filter(
            id=request.POST.get('category'),
            category_type='expense'
        ).first()
        payment_mode = PaymentMode.objects.filter(id=request.POST.get('payment_mode')).first()

        if not category or not payment_mode:
            messages.error(request, "Please select a valid category and payment mode.")
        else:
            try:
                exp.amount = Decimal(request.POST.get('amount'))
            except Exception:
                messages.error(request, "Please enter a valid amount.")
            else:
                exp.category = category
                exp.payment_mode = payment_mode
                exp.date = request.POST.get('date') or exp.date
                exp.description = (request.POST.get('description') or '').strip()
                exp.save()
                messages.success(request, "Expense updated successfully.")
                return redirect('expense_list')

    return render(request, 'forecast_app/edit_expense.html', {
        'expense': exp,
        'categories': categories,
        'payment_modes': payment_modes,
    })

@login_required
def delete_expense(request, pk):
    get_object_or_404(
        _scope_queryset_for_user(Transaction.objects.filter(transaction_type='expense'), request.user),
        pk=pk
    ).delete()
    return redirect('expense_list')

# ────────────────────────────────────────────────────────────
# RECEIVABLES / PAYABLES / AUTH / MISC
# ────────────────────────────────────────────────────────────

@login_required
def Rectable(request):
    receivable_scope = _scope_queryset_for_user(Receivable.objects.all(), request.user)
    party = request.GET.get("party", "").strip()
    due_date = request.GET.get("due_date", "").strip()

    recs = receivable_scope
    if party:
        recs = recs.filter(party_name__icontains=party)
    if due_date:
        recs = recs.filter(due_date=due_date)

    party_list = (
        receivable_scope
        .values_list("party_name", flat=True)
        .distinct()
        .order_by("party_name")
    )

    return render(request, "forecast_app/rectable.html", {
        "recs": recs.order_by("-due_date", "-id"),
        "party": party,
        "due_date": due_date,
        "party_list": party_list,
        "is_admin_view": True,
    })

@login_required
def Recform(request): return render(request, 'forecast_app/recform.html', {'form': ReceivableForm()})

@login_required
def Recievable_form(request):
    if request.method == "POST":
        f = ReceivableForm(request.POST); 
        if f.is_valid(): r = f.save(commit=False); r.user = request.user; r.save(); return redirect("rectable")
    return redirect("recform")

@login_required
def Recupdate(request, id):
    r = get_object_or_404(_scope_queryset_for_user(Receivable.objects.all(), request.user), id=id)
    if request.method == "POST":
        f = ReceivableForm(request.POST, instance=r)
        if f.is_valid(): f.save(); return redirect("rectable")
    return render(request, 'forecast_app/recupdate.html', {'recer': r})

@login_required
def Recdelete(request, id): get_object_or_404(_scope_queryset_for_user(Receivable.objects.all(), request.user), id=id).delete(); return redirect("rectable")

@login_required
def Paytable(request):
    payable_scope = _scope_queryset_for_user(Payable.objects.all(), request.user)
    party = request.GET.get("party", "").strip()
    due_date = request.GET.get("due_date", "").strip()

    pays = payable_scope
    if party:
        pays = pays.filter(party_name__icontains=party)
    if due_date:
        pays = pays.filter(due_date=due_date)

    party_list = (
        payable_scope
        .values_list("party_name", flat=True)
        .distinct()
        .order_by("party_name")
    )

    return render(request, "forecast_app/paytable.html", {
        "pays": pays.order_by("-due_date", "-id"),
        "party": party,
        "due_date": due_date,
        "party_list": party_list,
        "is_admin_view": True,
    })

@login_required
def Payform(request): return render(request, 'forecast_app/payform.html', {'form': PayableForm()})

@login_required
def Payable_form(request):
    if request.method == "POST":
        f = PayableForm(request.POST)
        if f.is_valid(): p = f.save(commit=False); p.user = request.user; p.save(); return redirect("paytable")
    return redirect("payform")
@login_required
def Payupdate(request, id):
    p = get_object_or_404(_scope_queryset_for_user(Payable.objects.all(), request.user), id=id)
    if request.method == "POST":
        f = PayableForm(request.POST, instance=p)
        if f.is_valid(): f.save(); return redirect("paytable")
    return render(request, 'forecast_app/payupdate.html', {'payer': p})

@login_required
def Paydelete(request, id): get_object_or_404(_scope_queryset_for_user(Payable.objects.all(), request.user), id=id).delete(); return redirect("paytable")

@login_required
def Settable(request): return render(request, 'forecast_app/settable.html', {'sets': Settings.objects.filter(user=request.user)})

@login_required
def Setform(request): return render(request, 'forecast_app/setform.html', {'form': Settingsform()})

@login_required
def Settings_form(request):
    if request.method == "POST":
        f = Settingsform(request.POST)
        if f.is_valid(): s = f.save(commit=False); s.user = request.user; s.save(); return redirect("settable")
    return redirect("setform")

@login_required
def Setupdate(request, id):
    s = get_object_or_404(Settings, id=id, user=request.user)
    if request.method == "POST":
        f = Settingsform(request.POST, instance=s)
        if f.is_valid(): f.save(); return redirect("settable")
    return render(request, 'forecast_app/setupdate.html', {'form': Settingsform(instance=s)})

@login_required
def Setdelete(request, id): get_object_or_404(Settings, id=id, user=request.user).delete(); return redirect("settable")

def login_view(request):
    if request.method == "POST":
        u = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if u: login(request, u); return redirect("dashboard")
        messages.error(request, "Invalid Credentials")
    return render(request, "forecast_app/login.html")

def register_view(request):
    if request.method == "POST":
        f = RegisterForm(request.POST)
        if f.is_valid(): f.save(); return redirect("login")
    return render(request, "forecast_app/register.html", {"form": RegisterForm()})

@login_required
def alerts(request):
    today = timezone.localdate()
    pending_receivables = _scope_queryset_for_user(
        Receivable.objects.filter(is_received=False),
        request.user
    ).select_related('user').order_by('due_date')
    pending_payables = _scope_queryset_for_user(
        Payable.objects.filter(is_paid=False),
        request.user
    ).select_related('user').order_by('due_date')

    def build_due_status(due_date):
        days_left = (due_date - today).days
        if days_left < 0:
            overdue_days = abs(days_left)
            unit = "day" if overdue_days == 1 else "days"
            return {
                "priority": 0,
                "label": f"Overdue by {overdue_days} {unit}",
                "badge_bg": "bg-red-100",
                "badge_text": "text-red-700",
            }
        if days_left == 0:
            return {
                "priority": 1,
                "label": "Due today",
                "badge_bg": "bg-orange-100",
                "badge_text": "text-orange-700",
            }
        if days_left <= 7:
            unit = "day" if days_left == 1 else "days"
            return {
                "priority": 2,
                "label": f"Due in {days_left} {unit}",
                "badge_bg": "bg-yellow-100",
                "badge_text": "text-yellow-700",
            }
        return {
            "priority": 3,
            "label": "Upcoming",
            "badge_bg": "bg-blue-100",
            "badge_text": "text-blue-700",
        }

    financial_alerts = []

    for rec in pending_receivables:
        due_status = build_due_status(rec.due_date)
        financial_alerts.append({
            "priority": due_status["priority"],
            "kind": "receivable",
            "title": f"Pending receivable from {rec.party_name}",
            "message": "Follow up and collect the pending amount.",
            "owner": rec.user.username,
            "amount": rec.amount,
            "due_date": rec.due_date,
            "status_label": due_status["label"],
            "badge_bg": due_status["badge_bg"],
            "badge_text": due_status["badge_text"],
            "icon": "fa-hand-holding-dollar",
            "icon_bg": "bg-green-100",
            "icon_text": "text-green-700",
            "amount_text": "text-green-600",
            "action_url": reverse('rectable'),
            "action_label": "View Receivables",
        })

    for pay in pending_payables:
        due_status = build_due_status(pay.due_date)
        financial_alerts.append({
            "priority": due_status["priority"],
            "kind": "payable",
            "title": f"Pending payable to {pay.party_name}",
            "message": "Schedule this payment to avoid delays or penalties.",
            "owner": pay.user.username,
            "amount": pay.amount,
            "due_date": pay.due_date,
            "status_label": due_status["label"],
            "badge_bg": due_status["badge_bg"],
            "badge_text": due_status["badge_text"],
            "icon": "fa-file-invoice-dollar",
            "icon_bg": "bg-red-100",
            "icon_text": "text-red-700",
            "amount_text": "text-red-600",
            "action_url": reverse('paytable'),
            "action_label": "View Payables",
        })

    financial_alerts.sort(key=lambda item: (item["priority"], item["due_date"], item["kind"]))

    receivable_total = pending_receivables.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    payable_total = pending_payables.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    context = {
        'financial_alerts': financial_alerts,
        'pending_receivable_count': pending_receivables.count(),
        'pending_payable_count': pending_payables.count(),
        'pending_receivable_total': receivable_total,
        'pending_payable_total': payable_total,
        'pending_net': receivable_total - payable_total,
        'legacy_alerts': Alert.objects.filter(user=request.user).order_by('-created_at'),
    }
    return render(request, 'forecast_app/alerts.html', context)

@login_required
def toggle_single_alert(request, alert_type): return redirect('alerts')

@login_required
def delete_alert(request, pk): get_object_or_404(Alert, pk=pk, user=request.user).delete(); return redirect('alerts')

def forecast_analytics(request): return render(request, 'forecast_app/forecast_analytics.html')
def receivables_payables(request): return render(request, 'forecast_app/receivables_payables.html')
def income_summary(request): return render(request, 'forecast_app/inc_summary.html')
def expense_summary(request): return render(request, 'forecast_app/expense_summary.html')
def avg_current_balance(request): return render(request, 'forecast_app/avg_balance.html')
def export_data(request): return HttpResponse("CSV Export")
def rp_home(request): return render(request, 'forecast_app/rec_pay.html')
