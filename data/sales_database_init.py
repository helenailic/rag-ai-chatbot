# sales_database_init.py
import sqlite3
import pandas as pd
import os

def initialize_sales_database(csv_file_path):
    """Initialize the sales database from CSV file"""
    try:
        # Verify the CSV file exists
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found at: {csv_file_path}")
            
        # Create or connect to database
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        
        # Drop existing table
        cursor.execute('DROP TABLE IF EXISTS events')
        
        # Create new table
        cursor.execute('''
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            "Sale Date" TEXT,
            "External Order Number" TEXT,
            "Exchange" TEXT,
            "Event" TEXT,
            "Venue" TEXT,
            "Event Date" TEXT,
            "Event Time" TEXT,
            "Section" TEXT,
            "Row" TEXT,
            "Low Seat" INTEGER,
            "High Seat" INTEGER,
            "Quantity" INTEGER,
            "Sale Currency" TEXT,
            "Gross Sale" REAL,
            "Gross Sale USD" REAL,
            "Fee" REAL,
            "Fee USD" REAL,
            "Net Sale" REAL,
            "Net Sale USD" REAL,
            "Cost" REAL,
            "Cost USD" REAL,
            "Profit" REAL,
            "Profit Percentage" REAL,
            "Tags" TEXT,
            "PO Currency" TEXT,
            "Region" TEXT,
            "Event Status" TEXT,
            "SH Event ID" TEXT,
            "Performer" TEXT
        )
        ''')

        # Read CSV file
        print("Reading CSV file...")
        df = pd.read_csv(csv_file_path)
        
        # Insert data into table
        print("Inserting data into database...")
        df.to_sql('events', conn, if_exists='replace', index=False)
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        print(f"Successfully inserted {count} records")
        
        conn.commit()
        conn.close()
        print("Sales database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing sales database: {str(e)}")
        return False

if __name__ == "__main__":
    # Update this path to your actual CSV file location
    csv_file_path = 'ta_example_data.csv'
    initialize_sales_database(csv_file_path)