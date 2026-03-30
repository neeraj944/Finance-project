from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login_view, name="login"),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ML Training Trigger
    path('train-models/', views.run_trainer, name='run_trainer'),
    path('api/predict-cashflow/', views.predict_cashflow_api, name='predict_api'),

    # Income CRUD
    path('income/add/', views.add_income, name='add_income'),
    path('income/list/', views.income_list, name='income_list'),
    path('income/edit/<int:pk>/', views.edit_income, name='edit_income'),
    path('income/delete/<int:pk>/', views.delete_income, name='delete_income'),

    # Expense CRUD
    path('expense/add/', views.add_expense, name='add_expense'),
    path('expense/list/', views.expense_list, name='expense_list'),
    path('expense/edit/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('expense/delete/<int:pk>/', views.delete_expense, name='delete_expense'),

    # Receivables
    path('rect/', views.Rectable, name='rectable'),
    path('recform/', views.Recform, name='recform'),
    path('recpy/', views.Recievable_form, name='recpy'),
    path('recup/<int:id>/', views.Recupdate, name='recup'),
    path('recdl/<int:id>/', views.Recdelete, name='recdl'),

    # Payables
    path('payt/', views.Paytable, name='paytable'),
    path('payform/', views.Payform, name='payform'),
    path('paypy/', views.Payable_form, name='paypy'),
    path('payup/<int:id>/', views.Payupdate, name='payup'),
    path('paydl/<int:id>/', views.Paydelete, name='paydl'),

    # Settings & Auth
    path('sett/', views.Settable, name='settable'),
    path('setform/', views.Setform, name='setfrom'),
    path('setpy/', views.Settings_form, name='setpy'),
    path('setup/<int:id>/', views.Setupdate, name='setup'),
    path('setdl/<int:id>/', views.Setdelete, name='setdl'),
    path('reg/', views.register_view, name='reg'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Analytics & Alerts
    path('alerts/', views.alerts, name='alerts'),
    path('alerts/toggle/<str:alert_type>/', views.toggle_single_alert, name='toggle_single_alert'),
    path('alerts/delete/<int:pk>/', views.delete_alert, name='delete_alert'),
    path('income-summary/', views.income_summary, name='income_summary'),
    path('expense-summary/', views.expense_summary, name='expense_summary'),
    path('avg-current-balance/', views.avg_current_balance, name='avg-current-balance'),
    path('forecast-analytics/', views.forecast_analytics, name='forecast_analytics'),
    path('export/', views.export_data, name='export_data'),
    path('rec-pay/', views.rp_home, name='rp_home'),
]