# discovery_manager.py
import requests
from typing import Dict, List, Optional
import json
from openai import OpenAI

class DiscoveryManager:
    def __init__(self, api_key: str = 'JRhz8tECTEsKfmdJWbyQuWylUFsjQxbM', openai_key: str = None):
        # api_key is the from the TicketMaster Developer Portal (set up company account or 
        # connect to unique API key above instead of JRhz8tECTEsKfmdJWbyQuWylUFsjQxbM)
        self.api_key = api_key
        self.base_url = 'https://app.ticketmaster.com/discovery/v2/events.json'
        self.openai_client = OpenAI(api_key=openai_key) if openai_key else None

    def parse_query(self, user_query: str) -> Dict:
        """Parse query using OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a data analyst that interacts with ticketing data. Parse the query to extract search parameters."},
                    {"role": "user", "content": user_query}
                ],
                # Assistants API function calling feature will specify the function, 
                # detect keywords within the query, and pass them as parameters to the 
                # function that calls the TicketMaster Discovery API
                functions=[{
                    "name": "fetch_ticketmaster_events",
                    "description": "Fetches events from Ticketmaster based on search parameters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "stateCode": {
                                "type": "string",
                                "description": "State code to filter events"
                            },
                            "city": {
                                "type": "string",
                                "description": "The city to search for events"
                            },
                            "size": {
                                "type": "number",
                                "description": "Number of events to return"
                            },
                            "keyword": {
                                "type": "string",
                                "description": "Keyword to filter events"
                            }
                        }
                    }
                }],
                function_call={"name": "fetch_ticketmaster_events"}
            )

            if response.choices[0].message.function_call:
                args = json.loads(response.choices[0].message.function_call.arguments)
                return args
            return {}
        except Exception as e:
            print(f"Error parsing query: {e}")
            return {}
            
    # this is the function that, given keywords/ arguments, will call the TicketMaster API and return filtered results
    def fetch_events(self, keyword: str = "", city: str = "", size: int = 20, stateCode: str = "") -> List:
        params = {
            "apikey": self.api_key,
            "size": size,
            "countryCode": "US"
        }
        
        if city:
            params["city"] = city
        if keyword:
            params["keyword"] = keyword
        if stateCode:
            params["stateCode"] = stateCode

        print(f"API params: {params}")
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        return data.get('_embedded', {}).get('events', [])

    def get_events(self, user_query: str) -> str:
        """Main method to handle event queries"""
        search_params = self.parse_query(user_query)
        events = self.fetch_events(**search_params)
        return self.format_event_response(events)
        
    # this function simply formats the json response from the TicketMaster API
    def format_event_response(self, events: List[Dict]) -> str:
        if not events:
            return "No upcoming events found. Try modifying your search terms."
            
        response = []
        response.append("\nUpcoming Events")
        response.append("-" * 80)
        
        for event in events:
            # Event name and date
            event_date = event['dates']['start'].get('localDate', 'TBA')
            event_time = event['dates']['start'].get('localTime', 'TBA')
            response.append(f"{event['name']}")
            response.append(f"Date: {event_date} at {event_time}")
            
            # Venue info
            if event.get('_embedded', {}).get('venues'):
                venue = event['_embedded']['venues'][0]
                location = f"{venue.get('city', {}).get('name', '')}, {venue.get('state', {}).get('stateCode', '')}"
                response.append(f"Location: {venue['name']} - {location}")
            
            # Price info - handle missing prices
            if event.get('priceRanges'):
                price = event['priceRanges'][0]
                if 'min' in price and 'max' in price:
                    response.append(f"Prices: ${price['min']:.2f} - ${price['max']:.2f}")
            
            # Ticket link
            if event.get('url'):
                response.append(f"Tickets: {event['url']}")
                
            response.append("-" * 80)
        
        return "\n".join(response)
