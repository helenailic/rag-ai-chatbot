from flask import Flask, request, jsonify, send_file
from openai import OpenAI
import os
from dotenv import load_dotenv
from flask_cors import CORS
from discovery import DiscoveryManager
from sales_manager import SalesManager
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import csv

# Import your existing system
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

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

# Initialize query processor
query_processor = QueryProcessor(API_KEY)

# Dictionary to store pending price changes
# Format: {user_id: {'event_name': str, 'current_price': float, 'new_price': float}}
price_changes = {}

client_id = '048a9b6221684456ba2799a4c672a70e'
client_secret = 'd2b43526da2b45c8aace915b58b4e679'
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def write_to_csv(data, filename="top_tracks.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["name", "artist", "album", "release_date"])
        writer.writeheader()
        writer.writerows(data)

def format_top_tracks(tracks):
    formatted_tracks = "\n".join(
        [f"{i+1}. {track['name']} by {track['artist']} from the album '{track['album']}'" for i, track in enumerate(tracks)]
    )
    return f"Here are the top tracks:\n{formatted_tracks}"

def handle_data_query(user_message, interpretation, user_id):
    """Handle data-related queries"""
    print("Starting data query handling...")
    with EventManager() as event_manager:
        print("Database connection established")
        
        action = interpretation.get('action')
        event_name = extract_event_name(interpretation)
        field = interpretation.get('field')
        increment = interpretation.get('number')
        
        print(f"Detected action: {action}, event: {event_name}, field: {field}, increment: {increment}")
        
        response = "I'll help you with that data request.\n\n"
        
        if action == "view":
            print("Handling view action...")
            # ... rest of view code ...

        elif field == "ticket_price" and action in ['increase', 'decrease', 'change', 'modify', 'update']:
            print("Handling price modification...")
            try:
                # First verify the event exists
                if not event_name:
                    return "Please specify an event name."
                
                # Get current price with error handling
                current_price = event_manager.get_event_value(event_name, 'ticket_price')
                if current_price is None:
                    return f"Could not find event '{event_name}' in the database."
                
                current_price = float(current_price)  # Convert to float after verifying not None
                print(f"Current price: ${current_price}")
                
                if increment is None:
                    return f"Please specify the amount to {action} the price by."
                
                # Calculate new price
                print(f"Calculating new price with action: {action} and increment: {increment}")
                new_price = calculate_new_price(action, action, current_price, increment)
                print(f"New price: ${new_price}")
                
                if new_price < 0:
                    return "Price cannot be negative. Operation cancelled."

                # Store the pending change
                price_changes[user_id] = {
                    'event_name': event_name,
                    'current_price': current_price,
                    'new_price': new_price
                }
                print(f"Stored pending change: {price_changes[user_id]}")

                # Format response with confirmation request
                response = format_price_message(event_name, current_price, new_price, action, action)
                response += "\n\nTo confirm this price change, reply with one of these:"
                response += f"\n1. 'confirm price change for {event_name}'"
                response += "\n2. 'cancel price change'"
                
            except ValueError as e:
                print(f"ValueError in price modification: {str(e)}")
                response = f"Error processing price modification: {str(e)}"
            except Exception as e:
                print(f"Unexpected error in price modification: {str(e)}")
                response = f"Error: Could not process the price change. Please verify the event name and try again."

        return response

#Function to get specific event name, filtering out filler words that might appear in a user's query
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
def handle_price_confirmation(user_message, user_id):
    """Handle price change confirmation messages"""
    if user_id not in price_changes:
        return None
        
    pending = price_changes[user_id]
    event_name = pending['event_name']
    
    if 'confirm price change for' in user_message.lower():
        if event_name.lower() in user_message.lower():
            try:
                with EventManager() as event_manager:
                    # Execute the price update
                    current_value, new_value = event_manager.update_event(
                        event_name=event_name,
                        field='ticket_price',
                        value=pending['new_price']
                    )
                    
                    # Clear the pending change
                    del price_changes[user_id]
                    
                    return f"Success! Price updated for {event_name}!\n" + \
                           f"Old price: ${current_value:.2f}\n" + \
                           f"New price: ${new_value:.2f}"
                           
            except Exception as e:
                return f"Error updating price: {str(e)}"
                
    elif 'cancel price change' in user_message.lower():
        # Clear the pending change
        del price_changes[user_id]
        return "Price change cancelled."
        
    return None

#backend route for chatbot
@app.route('/chat', methods=['POST'])
def chat():
    try:
        #the request (ie user message) as a json
        print("Received request data:", request.json)
        
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
            
        user_id = data.get('user_id', 'default_user')
        print(f"Processing message: {user_message}")
        past_indicators = ['previous', 'past', 'last', 'before', 'historical', 'history']
        if any(indicator in user_message for indicator in past_indicators):
            print("Historical query detected - using assistant")
            # Use the assistant for historical data
            thread = client.beta.threads.create()
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_message
            )
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID
            )
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_message = messages.data[0].content[0].text.value
            return jsonify({"response": assistant_message})
        # Check for discovery/event requests
        def is_event_query(message):
            event_words = ['event', 'events', 'show', 'shows', 'game', 'games', 'concert', 'concerts', 'upcoming']
            return any(word in message for word in event_words)

        if is_event_query(user_message):
            discovery_manager = DiscoveryManager(openai_key=os.getenv('OPENAI_API_KEY'))
            response = discovery_manager.get_events(user_message)
            return jsonify({"response": response})

        #check if it's a sales report query
        elif "sales report" in user_message.lower():
            sales_manager = SalesManager()
            response = sales_manager.generate_report(user_message)
            return jsonify({"response": response})
        #check if it's a data query
        data_keywords = ['event', 'ticket', 'price', 'display', 'all', 'increase', 'decrease', 'set']

        #check if this is a price confirmation message or regular message
        if user_id in price_changes:
            confirmation_response = handle_price_confirmation(user_message, user_id)
            if confirmation_response:
                return jsonify({"response": confirmation_response})    
        elif any(keyword in user_message.lower() for keyword in data_keywords):
            try:
                corrected_query = correct_spelling(user_message)
                interpretation = query_processor.interpret_query(corrected_query)
                print(f"Query interpretation: {interpretation}")

                if interpretation and interpretation.get('action'):
                    response = handle_data_query(user_message, interpretation, user_id)
                    return jsonify({"response": response})
                    
            except Exception as e:
                print(f"Error in data processing: {str(e)}")
                return jsonify({"error": f"Error processing data query: {str(e)}"}), 500

        #if not any of the other features, use the regular assistant to respond
        print("Using assistant for response")
        print(user_message)
        thread = client.beta.threads.create()
        
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        assistant_message = messages.data[0].content[0].text.value

        return jsonify({
            "response": assistant_message
        })

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/')
def home():
    #simple frontend 
    return send_file('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
