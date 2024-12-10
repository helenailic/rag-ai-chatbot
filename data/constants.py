# API configuration
API_KEY = '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'  # Replace with your OpenAI API key
DATABASE_PATH = 'sales_database.db'
EMBEDDING_CACHE_FILE = "column_embeddings_cache.json"

# Action groups mapping
ACTION_GROUPS = {
    "increase": ["increase", "markup", "add", "raise", "increment", "boost", "enhance", "up", "grow"],
    "decrease": ["decrease", "markdown", "subtract", "lower", "reduce", "lessen", "drop", "down", "shrink"],
    "change": ["change", "modify", "set", "update", "make", "change to", "set to"],
    "multiply": ["multiply", "times", "multiplied by", "mult", "double", "triple", "quadruple"],
    "divide": ["divide", "split by", "divided by", "div", "half", "halve"],
    "view": ["view", "show", "display", "see", "check", "tell me", "what is", "what's", "how many", "list", "get"],
    "report": ["report", "show report", "generate report", "sales report", "view report"],
    "discover": ["find events", "search events", "show events", "get events"]
}

# Protected columns that can't be modified
PROTECTED_COLUMNS = ["num_tickets", "event_name", "id", "venue", "event_date", "section", "row", "region", "performer"]

# Field mapping for embedding matching
FIELD_MAPPINGS = {
    "price": ["ticket_price", "cost", "price", "fare", "fee"],
    "event": ["event_name", "name", "event", "show", "game", "concert"],
    "venue": ["venue", "location", "arena", "stadium", "place"],
    "date": ["event_date", "date", "when", "time"],
    "tickets": ["num_tickets", "tickets", "quantity", "available"]
}

# Prompt templates
QUERY_INTERPRETATION_PROMPT = """
Interpret this query: '{query}' and return a JSON object with these keys:
- action_word: Extract the exact word or phrase used in the query that indicates the action
- event_name: Extract any event identifier or name mentioned
- field: what field to access (price, tickets, id, name, etc.)
- number: the amount to change by, multiply by, or divide by (null if viewing)

Examples:
- For "increase Bulls game ticket price by 100", return:
{{"action_word": "increase", "event_name": "Bulls game", "field": "ticket price", "number": 100}}
- For "show me Yankees vs Red Sox tickets", return:
{{"action_word": "show", "event_name": "Yankees vs Red Sox", "field": "tickets", "number": null}}
- For "what's happening at United Center", return:
{{"action_word": "what's", "event_name": "United Center", "field": "event_name", "number": null}}
"""