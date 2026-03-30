import os
import sys
import django
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# 1. FORCE THE PATHS
# This is the folder that contains manage.py
project_home = "/Users/neerajkp/Desktop/finance_project /finance_project/finance_project/cash_flow"
# This is the folder that contains settings.py (Notice the space!)
settings_dir = "/Users/neerajkp/Desktop/finance_project /finance_project/finance_project/cash_flow/finance_project"

sys.path.insert(0, project_home)
sys.path.insert(0, settings_dir)

# 2. BOOTSTRAP DJANGO
# We use the absolute name of the settings folder
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_project.settings')

try:
    django.setup()
    print(f"✅ SUCCESS: Django environment loaded!")
except Exception as e:
    print(f"❌ Still failing. Let's try the fallback...")
    # FALLBACK: If the above fails, your settings folder likely HAS the space in its name
    os.environ['DJANGO_SETTINGS_MODULE'] = 'finance_project .settings'
    try:
        django.setup()
        print(f"✅ SUCCESS: Django loaded (using the space-path fallback)!")
    except Exception as e2:
        print(f"❌ Critical Error: {e2}")
        sys.exit(1)

from forecast_app.models import Transaction
# ... rest of the code remains the same

# 3. SETUP MODEL DIRECTORIES (Inside ml_engine)
current_file_path = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(current_file_path, 'models')
INCOME_DIR = os.path.join(MODELS_DIR, 'income_models')
EXPENSE_DIR = os.path.join(MODELS_DIR, 'expense_models')

def clean_old_models():
    """Deletes old corrupted .pkl files to prevent STACK_GLOBAL errors"""
    for folder in [INCOME_DIR, EXPENSE_DIR]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                if file.endswith(".pkl"):
                    os.remove(os.path.join(folder, file))
            print(f"🧹 Cleaned old models from: {os.path.basename(folder)}")
        else:
            os.makedirs(folder, exist_ok=True)

def train_from_db():
    # 4. PULL DATA FROM DATABASE
    # We use 'category__name' to get the string name of the category
    queryset = Transaction.objects.all().values('amount', 'date', 'transaction_type', 'category__name')
    df = pd.DataFrame(list(queryset))

    if df.empty:
        print("❌ Database is empty. Add some transactions first!")
        return

    # 5. PREPROCESS DATA
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    df.rename(columns={'category__name': 'category'}, inplace=True)

    clean_old_models()

    # 6. TRAIN PER CATEGORY
    # This loop handles both Income and Expense folders
    for t_type in ['income', 'expense']:
        target_dir = INCOME_DIR if t_type == 'income' else EXPENSE_DIR
        type_df = df[df['transaction_type'] == t_type]
        
        unique_categories = type_df['category'].unique()
        
        for cat in unique_categories:
            if not cat: continue # Skip empty categories
            
            cat_df = type_df[type_df['category'] == cat]
            
            # Group by Month/Year to get the total amount for that period
            m_data = cat_df.groupby(['year', 'month'])['amount'].sum().reset_index()

            # We train with Month and Year as the only 2 features
            X = m_data[['month', 'year']]
            y = m_data['amount']

            # Using Random Forest (Standard and robust)
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)

            # 7. SAVE FRESH MODELS
            # Saving in 'wb' (Write Binary) fixes the invalid load key errors
            file_name = f"{cat.lower().replace(' ', '_')}.pkl"
            file_path = os.path.join(target_dir, file_name)
            
            with open(file_path, 'wb') as f:
                pickle.dump(model, f)
            
            print(f"✨ Trained & Saved Model: {cat}")

if __name__ == "__main__":
    train_from_db()
    print("🚀 All models are now up-to-date and compatible with your Mac!")