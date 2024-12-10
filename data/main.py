from database_manager import EventManager
from query_processor import QueryProcessor
from utilities import (
    correct_spelling, 
    calculate_new_price, 
    format_price_message,
    validate_price,
    extract_event_name
)
from constants import API_KEY, PROTECTED_COLUMNS

def process_price_modification(event_manager, event_name, field, action, matched_action, increment, specific_id=None):
    """Process price modification with validation"""
    try:
        # Use event ID if provided
        current_price = float(event_manager.get_event_value(event_name, field, specific_id))
        new_price = calculate_new_price(action, matched_action, current_price, increment)
        
        if new_price < 0:
            raise ValueError("Price cannot be negative")
            
        return current_price, new_price
    except ValueError as e:
        raise ValueError(f"Error processing price modification: {str(e)}")

def handle_view_action(event_manager, event_name, field, specific_id=None):
    """Handle view actions for different fields"""
    # Special case for viewing all events
    if event_name.lower() == 'all':
        print("\n=== All Events ===")
        event_manager.display_all_events()
        return

    # If specific ID is provided, show details for that event
    if specific_id:
        event_details = event_manager.get_event_by_id(specific_id)
        if event_details:
            print(f"\nEvent ID: {event_details[0]}")
            print(f"Name: {event_details[1]}")
            print(f"Price: ${event_details[2]:.2f}")
            print(f"Venue: {event_details[3]}")
            print(f"Date: {event_details[4]}")
            print("-" * 50)
        else:
            print(f"No event found with ID {specific_id}")
        return

    # If no specific field is mentioned, show all details
    if not field:
        matches = event_manager.get_matching_events(event_name, specific_id)
        if matches:
            print(f"\nFound {len(matches)} matching events:")
            for match in matches:
                print(f"\nEvent ID: {match[0]}")
                print(f"Name: {match[1]}")
                print(f"Price: ${match[2]:.2f}")
                print(f"Venue: {match[3]}")
                print(f"Date: {match[4]}")
                print("-" * 50)
        else:
            print(f"No events found matching '{event_name}'" + 
                  (f" with ID {specific_id}" if specific_id else ""))
        return

    value = event_manager.get_event_value(event_name, field, specific_id)
    if value is None:
        print(f"Could not find {field} for {event_name}" + 
              (f" with ID {specific_id}" if specific_id else ""))
        return
        
    if field == "ticket_price":
        print(f"The ticket price for {event_name}" + 
              (f" (ID: {specific_id})" if specific_id else "") + 
              f" is: ${value:.2f}")
    else:
        print(f"The {field} for {event_name}" + 
              (f" (ID: {specific_id})" if specific_id else "") + 
              f" is: {value}")

def extract_event_name(interpretation):
    """Extract the event name from the user input, filtering out common filler words."""
    event_name = interpretation.get('event_name', '')
    
    # List of filler words that are commonly used but not part of the event name
    filler_words = {'my', 'tickets', 'concert', 'show', 'event'}
    
    # Normalize input by converting to lowercase and removing filler words
    event_words = [word for word in event_name.lower().split() if word not in filler_words]
    
    # Reconstruct the event name after removing filler words
    normalized_event_name = ' '.join(event_words)
    
    return normalized_event_name.strip()

def ask_for_change_scope():
    """Ask user if they want to change all events or a specific ticket"""
    while True:
        scope_choice = input("Would you like to update all ticket prices for this event or a specific ticket? (Enter 'all' or 'ticket'): ").strip().lower()
        if scope_choice in ['all', 'ticket']:
            return scope_choice
        else:
            print("Invalid choice. Please enter 'all' or 'ticket'.")

def is_valid_event_id(event_manager, event_id):
    """Check if the event ID is valid"""
    event = event_manager.get_event_by_id(event_id)
    if event:
        return True
    return False

def confirm_change():
    """Ask for user confirmation before making changes"""
    while True:
        confirmation = input("Are you sure you want to make this change? (yes/no): ").strip().lower()
        if confirmation == 'yes':
            return True
        elif confirmation == 'no':
            print("Change canceled.")
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

# Update main parsing logic
def main():
    """Main execution function"""
    try:
        # Initialize components
        event_manager = EventManager()
        query_processor = QueryProcessor(API_KEY)

        # Display current data
        print("\n=== Current Event Data ===")
        event_manager.display_all_events()

        while True:
            # Get and process user query
            user_query = input("\nWhat would you like to do? (or 'exit' to quit) ").strip()
            
            if user_query.lower() in ['exit', 'quit']:
                break

            # Enhanced parsing to handle phrases like "Change Coldplay concert to 400 dollars"
            corrected_query = correct_spelling(user_query)
            if corrected_query != user_query:
                print(f"I corrected that to: {corrected_query}")

            # Process query
            interpretation = query_processor.interpret_query(corrected_query)
            if not interpretation:
                print("I couldn't understand your query.")
                continue

            # Extract query components
            action = interpretation.get('action')
            matched_action = interpretation.get('matched_action')
            event_name = extract_event_name(interpretation)
            field = interpretation.get('field', 'ticket_price')  # Default to ticket_price if not specified
            increment = interpretation.get('number') or extract_price_from_query(corrected_query)
            specific_id = interpretation.get('specific_id')

            if not event_name and action != 'view' and not specific_id:
                print("I couldn't determine which event you meant.")
                continue

            # Handle view action
            if action == "view":
                handle_view_action(event_manager, event_name or 'all', field, specific_id)
                continue

            # Handle modifications
            if field == "ticket_price":
                try:
                    current_price, new_price = process_price_modification(
                        event_manager, event_name, field, action, matched_action, increment, specific_id
                    )

                    # Ask the user whether to update all events or a specific ticket
                    change_scope = ask_for_change_scope()

                    if change_scope == 'ticket':
                        # Prompt for the Event ID to modify a specific ticket
                        event_id = input("Please enter the Event ID: ").strip()

                        try:
                            event_id = int(event_id)  # Ensure it's an integer
                            if is_valid_event_id(event_manager, event_id):
                                print(format_price_message(
                                    event_name, current_price, new_price, action, matched_action
                                ))

                                # Confirm before making the change
                                if confirm_change():
                                    print(f"\nSuccessfully updated the ticket price for event ID {event_id}!")
                                    event_manager.update_event(event_name, field, new_price, event_id)
                                else:
                                    print("No changes were made to the price.")

                            else:
                                print(f"No event found with ID {event_id}.")
                        except ValueError:
                            print("Invalid Event ID. Please enter a valid integer.")

                    elif change_scope == 'all':
                        print(format_price_message(
                            event_name, current_price, new_price, action, matched_action
                        ))
                        # Confirm before making the change to all events
                        if confirm_change():
                            event_manager.update_event(event_name, field, new_price)
                            print(f"\nSuccessfully updated the price for all events!")
                            event_manager.display_all_events()
                        else:
                            print("\nNo changes made.")
                
                except ValueError as e:
                    print(f"\nError: {e}")
            else:
                if field in PROTECTED_COLUMNS:
                    print(f"\nSorry, I can't modify the {field}. This field is protected.")
                    handle_view_action(event_manager, event_name, field, specific_id)
                else:
                    print(f"\nSorry, I can only modify ticket prices right now.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'event_manager' in locals():
            event_manager.close()

if __name__ == "__main__":
    main()
