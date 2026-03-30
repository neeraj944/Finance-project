import os
import pickle
import pandas as pd
from django.core.management.base import BaseCommand
from forecast_app.models import Transaction
from sklearn.ensemble import RandomForestRegressor

class Command(BaseCommand):
    help = 'Trains ML models from database transactions safely'

    def handle(self, *args, **kwargs):
        # 1. SETUP PATHS
        # Detects ml_engine folder relative to this management command
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ml_engine_dir = os.path.abspath(os.path.join(current_dir, "../../../ml_engine"))
        
        income_dir = os.path.join(ml_engine_dir, 'models', 'income_models')
        expense_dir = os.path.join(ml_engine_dir, 'models', 'expense_models')

        # Ensure directories exist
        os.makedirs(income_dir, exist_ok=True)
        os.makedirs(expense_dir, exist_ok=True)

        # 2. GET DATA FROM DATABASE
        # Pulls categories through the foreign key link
        queryset = Transaction.objects.all().values('amount', 'date', 'transaction_type', 'category__name')
        df = pd.DataFrame(list(queryset))

        if df.empty:
            self.stdout.write(self.style.ERROR("❌ No data found in database to train on."))
            return

        # Preprocessing
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df.rename(columns={'category__name': 'category'}, inplace=True)

        # 3. CLEAN OLD MODELS (Prevents STACK_GLOBAL errors)
        for d in [income_dir, expense_dir]:
            for f in os.listdir(d):
                if f.endswith('.pkl'):
                    os.remove(os.path.join(d, f))

        # 4. TRAINING LOOP
        for t_type in ['income', 'expense']:
            target_dir = income_dir if t_type == 'income' else expense_dir
            type_df = df[df['transaction_type'] == t_type]
            
            unique_categories = type_df['category'].unique()
            
            for cat in unique_categories:
                if not cat: continue
                
                # Filter data for this specific category
                cat_df = type_df[type_df['category'] == cat]
                
                # Group by Month/Year to get the sum
                m_data = cat_df.groupby(['year', 'month'])['amount'].sum().reset_index()

                # Basic check: We need at least 1 record to fit a model
                if m_data.empty:
                    continue

                X = m_data[['month', 'year']]
                y = m_data['amount']

                # Train Model
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X, y)

                # ✨ FILE SAVING LOGIC (The "Slash" Fix)
                # This replaces spaces and slashes with underscores so the file path is valid
                clean_name = str(cat).lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
                file_name = f"{clean_name}.pkl"
                file_path = os.path.join(target_dir, file_name)
                
                with open(file_path, 'wb') as f:
                    pickle.dump(model, f)
                
                self.stdout.write(self.style.SUCCESS(f"✅ Trained & Saved: {cat}"))

        self.stdout.write(self.style.SUCCESS("\n🚀 ALL MODELS REGENERATED SUCCESSFULLY!"))
        self.stdout.write(self.style.SUCCESS("Your dashboard predictions should now work without errors."))