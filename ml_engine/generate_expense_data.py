import sqlite3
import pandas as pd
import os
import sys
import django

# 1. Initialize Django environment (Required to use settings.BASE_DIR)
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cash_flow.settings') # Ensure this matches your project name
django.setup()

from django.conf import settings

def refresh_training_tables():
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    conn = sqlite3.connect(db_path, timeout=20)
    
    try:
        # Pull all transactions with category names
        query = """
        SELECT strftime('%Y-%m', t.date) as month_key, 
               t.amount, 
               c.name as category_name, 
               t.transaction_type
        FROM forecast_app_transaction t
        JOIN forecast_app_category c ON t.category_id = c.id
        ORDER BY t.date ASC
        """
        df_raw = pd.read_sql_query(query, conn)
        
        if df_raw.empty:
            print("No transaction data found.")
            return

        for t_type in ['income', 'expense']:
            # Filter by type (income or expense)
            df_type = df_raw[df_raw['transaction_type'] == t_type].copy()
            
            if df_type.empty:
                print(f"No {t_type} data found. Skipping...")
                continue

            # 1. PIVOT: Using 'sum' to get actual money amounts instead of 1/0 encodings
            pivot_df = df_type.pivot_table(index='month_key', 
                                          columns='category_name', 
                                          values='amount', 
                                          aggfunc='sum', 
                                          fill_value=0)

            # 2. Monthly Totals
            monthly_totals = df_type.groupby('month_key')['amount'].sum().rename(f'total_{t_type}')
            
            # Combine Total + Category Sums
            final_df = pd.concat([monthly_totals, pivot_df], axis=1).reset_index()

            # 3. Growth Calculation
            # (Current Month / Previous Month) -> 1.0 means no change, 1.1 means 10% growth
            final_df['growth'] = final_df[f'total_{t_type}'] / final_df[f'total_{t_type}'].shift(1)
            final_df.loc[0, 'growth'] = 1.0
            final_df['growth'] = final_df['growth'].fillna(1.0)

            # 4. Clean Column Names (Lowercase and underscores)
            final_df.columns = [c.replace(' ', '_').lower() for c in final_df.columns]

            # 5. Write to Database
            table_name = f'{t_type}_training_data'
            print(f"Attempting to write {table_name}...")
            
            # 'replace' handles the 1200+ categories by rebuilding the table structure automatically
            final_df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"✅ Success! {table_name} updated with actual sums.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    refresh_training_tables()