import os
import pickle
import pandas as pd
import numpy as np
from calendar import month_name
from .explanation import generate_financial_explanation
from forecast_app.models import Transaction

class FinancePredictor:
    def __init__(self):
        # Dynamically finds the 'ml_engine' folder you just created
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_model_path = os.path.join(current_dir, 'models')
        
        self.income_dir = os.path.join(self.base_model_path, 'income_models')
        self.expense_dir = os.path.join(self.base_model_path, 'expense_models')

    def _predict_from_folder(self, folder_path, year, month):
        total_sum = 0.0
        category_predictions = {}  # store predictions per category

        if not os.path.exists(folder_path):
            print(f"⚠️ Folder not found: {folder_path}")
            return 0.0, category_predictions

        model_files = [f for f in os.listdir(folder_path) if f.endswith('.pkl')]
        
        # Match the input format used in your trainer.py
        input_data = pd.DataFrame([[month, year]], columns=['month', 'year'])

        for file_name in model_files:
            file_path = os.path.join(folder_path, file_name)
            try:
                with open(file_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Ensure it's a valid model object
                if hasattr(model, 'predict'):
                    prediction = model.predict(input_data)
                    val = float(prediction[0])

                    category_name = file_name.replace(".pkl", "")
                    category_predictions[category_name] = val

                    total_sum += max(0, val)

                    print(f"✅ Predicted {file_name}: ₹{val:.2f}")

            except Exception as e:
                print(f"❌ Error loading {file_name}: {e}")
        
        return total_sum, category_predictions

    def _load_transaction_data(self, user_id):

        transactions = Transaction.objects.filter(user_id=user_id)

        data = []

        for t in transactions:
            data.append({
                "transaction_type": t.transaction_type,
                "category": t.category.name if t.category else "Uncategorized",
                "amount": float(t.amount)
            })

        df = pd.DataFrame(data, columns=["transaction_type", "category", "amount"])

        return df

    def _humanize_category(self, category_name):
        return str(category_name or "Uncategorized").replace("_", " ").title()

    def _build_income_suggestion(self, category_name):
        category = str(category_name or "").lower()
        if "rental" in category:
            return (
                "Maintaining consistent rental income streams can help ensure stable "
                "financial growth and improve monthly cash flow stability."
            )
        if "salary" in category:
            return (
                "Strengthening salary continuity and exploring increments can improve "
                "long-term cash flow reliability."
            )
        if "business" in category or "freelance" in category:
            return (
                "Diversifying client sources and retaining recurring contracts can improve "
                "income consistency month over month."
            )
        return (
            "Strengthening this income stream and keeping it consistent can improve "
            "overall monthly cash flow stability."
        )

    def _build_expense_suggestion(self, category_name):
        category = str(category_name or "").lower()
        if "grocery" in category:
            return (
                "Planning grocery purchases and setting weekly spending limits may help "
                "optimize overall monthly expenses."
            )
        if "rent" in category or "emi" in category:
            return (
                "Reviewing fixed obligations and negotiating better terms where possible "
                "may reduce pressure on monthly outflows."
            )
        if "shopping" in category or "entertainment" in category:
            return (
                "Setting stricter discretionary budgets can help control non-essential "
                "monthly spending."
            )
        return (
            "Tracking this category weekly and setting a spending cap can help optimize "
            "overall monthly expenses."
        )

    def _get_top_high_items(self, category_values, limit=3):
        top_items = []
        sorted_values = sorted(
            category_values.items(),
            key=lambda item: float(item[1]),
            reverse=True
        )

        for category, value in sorted_values[:limit]:
            numeric_value = round(float(value), 2)
            if numeric_value <= 0:
                continue
            top_items.append({
                "category": self._humanize_category(category),
                "value": numeric_value
            })

        return top_items

    def _build_ai_financial_insight(self, month, year, income_values, expense_values):
        month_label = f"{month_name[int(month)]} {int(year)}"
        insight = {
            "income_insight": "Run AI Forecast to generate income insight.",
            "income_suggestion": "Run AI Forecast to generate income suggestion.",
            "expense_insight": "Run AI Forecast to generate expense insight.",
            "expense_suggestion": "Run AI Forecast to generate expense suggestion.",
            "income_high_items": [],
            "expense_high_items": [],
        }

        if income_values:
            top_income_category = max(income_values, key=income_values.get)
            top_income_label = self._humanize_category(top_income_category)
            income_high_items = self._get_top_high_items(income_values)
            if income_high_items:
                high_income_names = ", ".join(item["category"] for item in income_high_items)
                high_income_line = f" Other high-value income categories included {high_income_names}."
            else:
                high_income_line = ""
            insight["income_insight"] = (
                f"In {month_label}, {top_income_label} contributed the highest share of total income, "
                "indicating a strong recurring revenue source for this month."
                f"{high_income_line}"
            )
            insight["income_suggestion"] = self._build_income_suggestion(top_income_category)
            insight["income_high_items"] = income_high_items

        if expense_values:
            top_expense_category = max(expense_values, key=expense_values.get)
            top_expense_label = self._humanize_category(top_expense_category)
            expense_high_items = self._get_top_high_items(expense_values)
            if expense_high_items:
                high_expense_names = ", ".join(item["category"] for item in expense_high_items)
                high_expense_line = f" Other high-value expense categories included {high_expense_names}."
            else:
                high_expense_line = ""
            insight["expense_insight"] = (
                f"In {month_label}, {top_expense_label} contributed the largest portion of expenses, "
                "suggesting that this category dominates the monthly budget."
                f"{high_expense_line}"
            )
            insight["expense_suggestion"] = self._build_expense_suggestion(top_expense_category)
            insight["expense_high_items"] = expense_high_items

        return insight

    def get_net_cash_flow(self, user_id, year, month):

        inc, income_predictions = self._predict_from_folder(self.income_dir, year, month)
        exp, expense_predictions = self._predict_from_folder(self.expense_dir, year, month)

        # Load transaction data (kept as you wrote it)
        df = self._load_transaction_data(user_id)

        # Keep this call (not removed)
        try:
            income_categories, expense_categories, _ = generate_financial_explanation(df)
        except Exception:
            income_categories, expense_categories = {}, {}

        # Prefer model predictions; fallback to historical category totals if models are unavailable.
        income_category_values = income_predictions or {
            key: float(value.get("amount", 0)) for key, value in income_categories.items()
        }
        expense_category_values = expense_predictions or {
            key: float(value.get("amount", 0)) for key, value in expense_categories.items()
        }
        insight = self._build_ai_financial_insight(month, year, income_category_values, expense_category_values)
        
        return {
            'total_income': round(inc, 2),
            'total_expense': round(exp, 2),
            'net_cash': round(inc - exp, 2),
            "income_categories": {k: round(float(v), 2) for k, v in income_category_values.items()},
            "expense_categories": {k: round(float(v), 2) for k, v in expense_category_values.items()},
            "ai_explanation": insight
        }
