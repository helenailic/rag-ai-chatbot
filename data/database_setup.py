import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime

def setup_database():
    # Connect to the SQLite database
    conn = sqlite3.connect('sales_database.db')
    cursor = conn.cursor()

    # Drop the existing events table if it exists
    cursor.execute('DROP TABLE IF EXISTS events')

    # Create a new table that matches our needs
    cursor.execute('''
    CREATE TABLE events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT NOT NULL,
        venue TEXT,
        event_date TEXT,
        section TEXT,
        row TEXT,
        ticket_price FLOAT NOT NULL,
        num_tickets INTEGER NOT NULL,
        embedding BLOB,  -- Added embedding column to store embeddings
        region TEXT,
        performer TEXT
    )
    ''')
    
    return conn, cursor

def load_csv_data(filename):
    """Load and preprocess the CSV data"""
    try:
        # Read the CSV file into a pandas DataFrame
        data = pd.read_csv(filename)
        
        # Convert data into the format we need
        processed_data = []
        for _, row in data.iterrows():
            # Parse the date
            try:
                event_date = datetime.strptime(row['Event Date'], '%m/%d/%y').strftime('%Y-%m-%d')
            except:
                event_date = None  # Handle invalid dates
            
            # Calculate ticket price per ticket (Gross Sale divided by Quantity)
            try:
                ticket_price = float(row['Gross Sale']) / float(row['Quantity']) if row['Quantity'] > 0 else 0
            except:
                ticket_price = 0  # Handle division errors
            
            processed_row = (
                row['Event'],  # event_name
                row['Venue'],  # venue
                event_date,    # event_date
                row['Section'],# section
                row['Row'],    # row
                ticket_price,  # ticket_price
                row['Quantity'],# num_tickets
                np.zeros(1536, dtype=np.float32).tobytes(),  # placeholder embedding
                row['Region'], # region
                row['Performer'] # performer
            )
            processed_data.append(processed_row)
            
        return processed_data
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return []

def insert_data(cursor, data):
    """Insert the processed data into the database"""
    cursor.executemany('''
    INSERT INTO events (
        event_name, venue, event_date, section, row, 
        ticket_price, num_tickets, embedding, region, performer
    ) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

def main():
    # Setup database
    conn, cursor = setup_database()
    
    try:
        # Load and process CSV data
        print("Loading CSV data...")
        processed_data = load_csv_data('ta_example_data.csv')  # Your CSV filename
        
        if processed_data:
            # Insert data into database
            print("Inserting data into database...")
            insert_data(cursor, processed_data)
            
            # Commit the changes
            conn.commit()
            
            # Display sample of the data
            print("\nSample of inserted data:")
            cursor.execute('''
                SELECT event_name, venue, event_date, ticket_price, num_tickets 
                FROM events LIMIT 5
            ''')
            for row in cursor.fetchall():
                print(f"Event: {row[0]}")
                print(f"Venue: {row[1]}")
                print(f"Date: {row[2]}")
                print(f"Price per ticket: ${row[3]:.2f}")
                print(f"Number of tickets: {row[4]}")
                print("-" * 50)
                
            # Get some statistics
            cursor.execute('SELECT COUNT(*) FROM events')
            total_events = cursor.fetchone()[0]
            print(f"\nTotal number of events in database: {total_events}")
            
        else:
            print("No data was processed. Please check the CSV file and try again.")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()