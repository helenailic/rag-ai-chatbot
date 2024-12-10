import sqlite3
from datetime import datetime

class EventManager:
    def __init__(self, db_path='sales_database.db'):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Context manager entry"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.conn:
            self.conn.close()

    def connect(self):
        """Explicit connection method"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

    def display_all_events(self):
        """Display all events in formatted table"""
        self.cursor.execute("""
            SELECT id, event_name, ticket_price, num_tickets, venue, event_date 
            FROM events
            ORDER BY event_date
        """)
        events = self.cursor.fetchall()
        
        output = []
        output.append(f"{'ID':<5} {'Event Name':<40} {'Ticket Price':<15} {'Num Tickets':<15} {'Venue':<30} {'Date'}")
        output.append("=" * 110)
        
        for event in events:
            output.append(f"{event[0]:<5} {event[1][:38]:<40} ${event[2]:<14.2f} {event[3]:<15} {event[4][:28]:<30} {event[5]}")
        
        return '\n'.join(output)

    def get_event_value(self, event_name, field, specific_id=None):
        """Get specific value for an event, optionally filtered by ID"""
        if specific_id:
            # If ID is specified, use exact ID match
            self.cursor.execute(f"""
                SELECT {field} 
                FROM events 
                WHERE id = ? AND event_name LIKE ? COLLATE NOCASE
            """, (specific_id, f'%{event_name}%'))
        else:
            # Otherwise use just the name match
            self.cursor.execute(f"""
                SELECT {field} 
                FROM events 
                WHERE event_name LIKE ? COLLATE NOCASE
            """, (f'%{event_name}%',))
        
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_event(self, event_name, field, value, specific_id=None):
        """Update event field with validation, optionally filtered by ID"""
        if field != 'ticket_price':
            raise ValueError(f"Cannot modify {field}. Only ticket prices can be modified.")
        
        if value < 0:
            raise ValueError("Price cannot be negative")

        # Get current value before update
        current_value = self.get_event_value(event_name, field, specific_id)
        if current_value is None:
            raise ValueError(f"Event not found: {event_name}" + (f" with ID {specific_id}" if specific_id else ""))

        if specific_id:
            # Update with specific ID
            self.cursor.execute(f"""
                UPDATE events 
                SET {field} = ? 
                WHERE id = ? AND event_name LIKE ? COLLATE NOCASE
            """, (value, specific_id, f'%{event_name}%'))
        else:
            # Update all matching events
            self.cursor.execute(f"""
                UPDATE events 
                SET {field} = ? 
                WHERE event_name LIKE ? COLLATE NOCASE
            """, (value, f'%{event_name}%'))
        
        self.conn.commit()
        return current_value, value

    def get_matching_events(self, event_name, specific_id=None):
        """Get all events matching a name pattern, optionally filtered by ID"""
        if specific_id:
            self.cursor.execute("""
                SELECT id, event_name, ticket_price, venue, event_date
                FROM events 
                WHERE id = ? AND event_name LIKE ? COLLATE NOCASE
                ORDER BY event_date
            """, (specific_id, f'%{event_name}%'))
        else:
            self.cursor.execute("""
                SELECT id, event_name, ticket_price, venue, event_date
                FROM events 
                WHERE event_name LIKE ? COLLATE NOCASE
                ORDER BY event_date
            """, (f'%{event_name}%',))
        
        return self.cursor.fetchall()

    def get_event_by_id(self, event_id):
        """Get specific event by ID"""
        self.cursor.execute("""
            SELECT id, event_name, ticket_price, venue, event_date
            FROM events 
            WHERE id = ?
        """, (event_id,))
        return self.cursor.fetchone()

    def get_all_events(self):
        """Get all events as a list"""
        self.cursor.execute("""
            SELECT id, event_name, ticket_price, num_tickets, venue, event_date 
            FROM events
            ORDER BY event_date
        """)
        return self.cursor.fetchall()

    def get_all_event_names(self):
        """Get list of all event names"""
        self.cursor.execute("SELECT DISTINCT event_name FROM events")
        return [row[0] for row in self.cursor.fetchall()]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None