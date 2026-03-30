import sqlite3
import pandas as pd
import os
import sys
import django

# 1. Initialize Django environment (needed if running as a standalone script)
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cash_flow.settings') 
django.setup()

from django.conf import settings

def refresh_income_training_table():
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    conn = sqlite3.connect(db_path, timeout=20)
    
    try:
        query = """
        SELECT strftime('%Y-%m', t.date) as month_key, t.amount, c.name as category_name
        FROM forecast_app_transaction t
        JOIN forecast_app_category c ON t.category_id = c.id
        WHERE t.transaction_type = 'income'
        ORDER BY t.date ASC
        """
        df_raw = pd.read_sql_query(query, conn)
        
        if df_raw.empty:
            print("No income data found.")
            return

        # 1. RAW SUMS: Pivot using 'sum' to get actual currency values (No 1s or 0s)
        pivot_df = df_raw.pivot_table(index='month_key', columns='category_name', 
                                       values='amount', aggfunc='sum', fill_value=0)

        # 2. Monthly Totals
        monthly_totals = df_raw.groupby('month_key')['amount'].sum().rename('total_income')
        final_df = pd.concat([monthly_totals, pivot_df], axis=1).reset_index()

        # 3. Growth Calculation (Current / Previous)
        # 1.0 = No change, 1.10 = 10% increase
        final_df['growth'] = final_df['total_income'] / final_df['total_income'].shift(1)
        
        # Set first month growth to 1.0 fix
        final_df.loc[0, 'growth'] = 1.0
        final_df['growth'] = final_df['growth'].fillna(1.0)

        # 4. Change month_key from '2025-01' to 'January'
        final_df['month_key'] = pd.to_datetime(final_df['month_key']).dt.month_name()

        # Clean Column Names (e.g., "Rental Income" -> "rental_income")
        final_df.columns = [c.replace(' ', '_').lower() for c in final_df.columns]

        print("Attempting to write Income Table...")
        # 'replace' automatically creates all category columns even if there are 1200+
        final_df.to_sql('income_training_data', conn, if_exists='replace', index=False)
        print("Success! Income training table updated with Actual Sums and Growth.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    refresh_income_training_table()