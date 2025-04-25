"""
Sample travel planning tool for DB-ADK.

This module contains a tool function for planning travel itineraries.
It demonstrates how to create a tool that can be used by agents.
"""

def plan_travel(destination: str, days: int, interests: list = None):
    """Plan a travel itinerary.
    
    Args:
        destination (str): Travel destination.
        days (int): Number of days for the trip.
        interests (list, optional): List of traveler interests. Defaults to None.
        
    Returns:
        dict: Travel itinerary with daily activities.
    """
    # This is a mock implementation
    # In a real application, this would call a travel API or database
    
    # Default interests if none provided
    if interests is None:
        interests = ["sightseeing", "food", "culture"]
    
    # Map interests to activities
    activity_map = {
        "sightseeing": [
            "Visit famous landmarks",
            "Take a guided city tour",
            "Explore historic sites"
        ],
        "food": [
            "Try local cuisine at a popular restaurant",
            "Visit a food market",
            "Take a cooking class"
        ],
        "culture": [
            "Visit museums and galleries",
            "Attend a cultural performance",
            "Explore local neighborhoods"
        ],
        "nature": [
            "Hike in nearby natural areas",
            "Visit parks and gardens",
            "Take a nature tour"
        ],
        "shopping": [
            "Visit local markets",
            "Shop at boutiques",
            "Explore shopping districts"
        ]
    }
    
    # Generate itinerary
    itinerary = {
        "destination": destination,
        "days": days,
        "interests": interests,
        "daily_plan": []
    }
    
    for day in range(1, days + 1):
        activities = []
        
        # Morning activity based on interests
        if "sightseeing" in interests or "culture" in interests:
            activities.append({
                "time": "Morning",
                "activity": activity_map["sightseeing" if day % 2 == 1 else "culture"][day % 3]
            })
        else:
            activities.append({
                "time": "Morning",
                "activity": activity_map[interests[0]][day % len(activity_map[interests[0]])]
            })
        
        # Afternoon activity
        if "food" in interests:
            activities.append({
                "time": "Afternoon",
                "activity": activity_map["food"][day % 3]
            })
        elif "shopping" in interests:
            activities.append({
                "time": "Afternoon",
                "activity": activity_map["shopping"][day % 3]
            })
        else:
            activities.append({
                "time": "Afternoon",
                "activity": activity_map[interests[-1]][day % len(activity_map[interests[-1]])]
            })
        
        # Evening activity
        activities.append({
            "time": "Evening",
            "activity": "Enjoy local nightlife and cuisine"
        })
        
        # Add day to itinerary
        itinerary["daily_plan"].append({
            "day": day,
            "activities": activities
        })
    
    return itinerary
