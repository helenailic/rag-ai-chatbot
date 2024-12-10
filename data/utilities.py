def correct_spelling(text):
    """Simple text cleanup without spell checking"""
    # Just clean up the text without spell checking
    return ' '.join(text.split())

def calculate_new_price(action, matched_action, current_price, increment):
    """Calculate new price based on action type"""
    try:
        if action == "multiply":
            multipliers = {"double": 2, "triple": 3, "quadruple": 4}
            factor = multipliers.get(matched_action, float(increment))
            return current_price * factor
        
        elif action == "divide":
            if matched_action in ["half", "halve"]:
                return current_price / 2
            return current_price / float(increment)
        
        elif action == "increase":
            return current_price + increment
        elif action in ['decrease', 'lower', 'reduce', 'drop', 'down']:
            return current_price - increment
        elif action in ['change', 'modify', 'set', 'update', 'make']:
            return increment  # For direct price setting, use the increment as the new price
        
        raise ValueError(f"Unknown action: {action}")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Error calculating new price: {str(e)}")

def format_price_message(event_name, current_price, new_price, action, matched_action):
    """Format price change message"""
    return f"""
Proposed change for {event_name}:
Action: {matched_action} ({action})
Current price: ${current_price:.2f}
New price will be: ${new_price:.2f}
"""

def format_event_details(event):
    """Format event details for display"""
    return f"""
Event Details:
Name: {event[1]}
Venue: {event[3]}
Date: {event[2]}
Current Price: ${event[4]:.2f}
Tickets Available: {event[5]}
"""

def validate_price(price):
    """Validate price value"""
    try:
        price = float(price)
        if price < 0:
            raise ValueError("Price cannot be negative")
        return price
    except (TypeError, ValueError):
        raise ValueError("Invalid price value")

def extract_event_name(interpretation):
    """Extract and clean event name from interpretation"""
    event_name = interpretation.get('event_name', '').strip()
    return event_name if event_name else None