"""
Sample logic module to demonstrate separation of concerns.
"""

def get_welcome_message() -> dict:
    """
    Returns a welcome message data structure.
    """
    return {
        "message": "Hello from the business logic layer!",
        "status": "success",
        "timestamp": "2024-01-01T00:00:00Z" 
    }
