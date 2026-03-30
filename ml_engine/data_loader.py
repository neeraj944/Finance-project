import sqlite3
import pandas as pd
import os
from django.conf import settings

def fetch_history_from_view(view_name):
    """
    Connects to the SQLite database and retrieves historical data 
    from the specified SQL view.
    """
    # Path to your db.sqlite3 file
    db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
    
    conn = sqlite3.connect(db_path)
    try:
        # Load the view into a Pandas DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {view_name} ORDER BY month_key ASC", conn)
    finally:
        conn.close()
    
    return df