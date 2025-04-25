"""
Sample weather tool for DB-ADK.

This module contains a tool function for getting weather information.
It demonstrates how to create a tool that can be used by agents.
"""

def get_weather(location: str, days: int = 3):
    """Get weather information for a location.
    
    Args:
        location (str): The location to get weather for (city, country).
        days (int, optional): Number of days for the forecast. Defaults to 3.
        
    Returns:
        dict: Weather information with current conditions and forecast.
    """
    # This is a mock implementation
    # In a real application, this would call a weather API
    
    # Generate mock weather data
    current = {
        "temperature": 25,
        "conditions": "Sunny",
        "humidity": 60,
        "wind_speed": 10
    }
    
    forecast = []
    for i in range(days):
        forecast.append({
            "day": i + 1,
            "temperature": 25 - i,
            "conditions": "Sunny" if i % 2 == 0 else "Partly Cloudy",
            "humidity": 60 + i * 2,
            "wind_speed": 10 - i
        })
    
    return {
        "location": location,
        "current": current,
        "forecast": forecast,
        "units": {
            "temperature": "Celsius",
            "wind_speed": "km/h"
        }
    }
