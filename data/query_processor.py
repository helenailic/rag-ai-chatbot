import os
import json
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from constants import API_KEY, EMBEDDING_CACHE_FILE, ACTION_GROUPS, QUERY_INTERPRETATION_PROMPT

FIELD_ALIASES = {
    "ticket_price": [
        "ticket price", "price", "prices", "cost", "fee", "fare", 
        "pricing", "ticket cost", "charge", "ticket", "tickets"  # Added "ticket" and "tickets"
    ],
    "num_tickets": [
        "number of tickets", "ticket count", "available tickets", 
        "remaining tickets", "quantity", "amount"
    ],
    "event_name": ["name", "event", "show", "game", "games", "concert", "concerts", "title"],
    "id": ["id", "identifier", "number"]
}

class QueryProcessor:
    def __init__(self, api_key=API_KEY):
        """Initialize query processor with API key"""
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.embedding_cache_file = EMBEDDING_CACHE_FILE
        self.cached_embeddings = self._load_cache()
        self.column_names = ["ticket_price", "num_tickets", "event_name", "id"]

    def _load_cache(self):
        """Load or initialize embedding cache"""
        try:
            if os.path.exists(self.embedding_cache_file):
                with open(self.embedding_cache_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
        return {}

    def _save_cache(self):
        """Save the current cache to file"""
        try:
            with open(self.embedding_cache_file, "w") as f:
                json.dump(self.cached_embeddings, f)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def get_embedding(self, text):
        """Get embedding with caching"""
        if not text:
            return None
            
        cache_key = str(text).lower().strip()
        if cache_key in self.cached_embeddings:
            return self.cached_embeddings[cache_key]

        url = "https://api.openai.com/v1/embeddings"
        data = {
            "model": "text-embedding-ada-002",
            "input": text
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                embedding = response.json()['data'][0]['embedding']
                self.cached_embeddings[cache_key] = embedding
                self._save_cache()
                return embedding
            else:
                print(f"API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error fetching embedding: {e}")
        return None

    def find_closest_match(self, query, options):
        """Find closest match using embeddings"""
        if not query or not options:
            return None

        query_embedding = self.get_embedding(str(query).lower().strip())
        if query_embedding is None:
            return None

        max_similarity = -1
        best_match = None

        for option in options:
            option_embedding = self.get_embedding(str(option).lower().strip())
            if option_embedding:
                similarity = cosine_similarity([query_embedding], [option_embedding])[0][0]
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = option

        return best_match

    def normalize_field(self, field_query):
        """Normalize field names using similarity matching"""
        if not field_query:
            return None
            
        # First try direct matching
        field_query = str(field_query).lower().strip()
        for db_field, aliases in FIELD_ALIASES.items():
            if field_query == db_field or field_query in aliases:
                return db_field
        
        # If no direct match, use embeddings similarity
        query_embedding = self.get_embedding(field_query)
        if query_embedding is None:
            return None

        max_similarity = -1
        best_field = None

        # Compare with main fields and their aliases
        for db_field, aliases in FIELD_ALIASES.items():
            # Try the main field name
            field_embedding = self.get_embedding(db_field)
            if field_embedding:
                similarity = cosine_similarity([query_embedding], [field_embedding])[0][0]
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_field = db_field
            
            # Try all aliases
            for alias in aliases:
                alias_embedding = self.get_embedding(alias)
                if alias_embedding:
                    similarity = cosine_similarity([query_embedding], [alias_embedding])[0][0]
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_field = db_field

        return best_field

    def _get_action_details(self, query_action):
        """Get base action and matched action for a query"""
        if not query_action:
            return None, None
            
        query_action = str(query_action).lower().strip()
        
        # Direct match first
        for base_action, action_words in ACTION_GROUPS.items():
            if query_action in action_words:
                return base_action, query_action
            
        # Similarity match if no direct match found
        closest_action = None
        best_base_action = None
        max_similarity = -1

        for base_action, action_words in ACTION_GROUPS.items():
            match = self.find_closest_match(query_action, action_words)
            if match:
                query_embedding = self.get_embedding(query_action)
                match_embedding = self.get_embedding(match)
                if query_embedding and match_embedding:
                    similarity = cosine_similarity([query_embedding], [match_embedding])[0][0]
                    if similarity > max_similarity:
                        max_similarity = similarity
                        closest_action = match
                        best_base_action = base_action

        return best_base_action, closest_action

    def interpret_query(self, query):
        """Interpret user query with enhanced error handling"""
        try:
            # Extract ID if present in query
            specific_id = None
            # Look for patterns like "id X", "#X", "ID: X", etc.
            id_patterns = [
                r'id\s+(\d+)',
                r'#(\d+)',
                r'ID:\s*(\d+)',
                r'number\s+(\d+)',
                r'with\s+id\s+(\d+)',
                r'id\s*=\s*(\d+)'
            ]
            
            import re
            for pattern in id_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    specific_id = int(match.group(1))
                    break

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "user", "content": QUERY_INTERPRETATION_PROMPT.format(query=query)}
                    ],
                    "max_tokens": 150
                }
            )
            
            if response.status_code == 200:
                interpretation = json.loads(response.json()['choices'][0]['message']['content'])
                
                # Get action details
                query_action = interpretation.get('action_word', '')
                base_action, matched_action = self._get_action_details(query_action)
                
                # Normalize the field using similarity matching
                field = interpretation.get('field')
                normalized_field = self.normalize_field(field)
                
                interpretation.update({
                    'action': base_action,
                    'matched_action': matched_action,
                    'field': normalized_field,
                    'original_query': query,
                    'specific_id': specific_id  # Add the extracted ID to the interpretation
                })
                
                return interpretation
            else:
                print(f"API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error interpreting query: {e}")
        return None