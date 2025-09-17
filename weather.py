#!/usr/bin/env python3
"""
Weather Data Fetcher

This script fetches current weather data from the National Weather Service
for a given ZIP code provided as a command line argument.
"""

import argparse
import json
import sys
from typing import Optional, Tuple, Dict, Any
import urllib.request
import urllib.parse
import urllib.error


class WeatherAPIError(Exception):
    """Custom exception for weather API errors."""
    pass


class WeatherFetcher:
    """Main class for fetching weather data."""
    
    def __init__(self):
        self.census_api_base = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        self.nws_api_base = "https://api.weather.gov"
    
    def get_coordinates_from_zip(self, zip_code: str) -> Tuple[float, float]:
        """
        Convert ZIP code to latitude/longitude using US Census Bureau API.
        
        Args:
            zip_code: US ZIP code string
            
        Returns:
            Tuple of (latitude, longitude)
            
        Raises:
            WeatherAPIError: If geocoding fails
        """
        if not zip_code or not zip_code.isdigit() or len(zip_code) != 5:
            raise WeatherAPIError(f"Invalid ZIP code format: {zip_code}")
        
        params = {
            'address': zip_code,
            'benchmark': '2020',
            'format': 'json'
        }
        
        url = f"{self.census_api_base}?{urllib.parse.urlencode(params)}"
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
        except urllib.error.URLError as e:
            raise WeatherAPIError(f"Failed to connect to geocoding service: {e}")
        except json.JSONDecodeError as e:
            raise WeatherAPIError(f"Failed to parse geocoding response: {e}")
        
        if not data.get('result', {}).get('addressMatches'):
            raise WeatherAPIError(f"ZIP code not found: {zip_code}")
        
        match = data['result']['addressMatches'][0]
        coords = match['coordinates']
        
        return float(coords['y']), float(coords['x'])  # lat, lon
    
    def get_weather_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get weather data from National Weather Service API.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary containing weather forecast data
            
        Raises:
            WeatherAPIError: If API request fails
        """
        # First, get the forecast office and grid coordinates
        points_url = f"{self.nws_api_base}/points/{latitude},{longitude}"
        
        try:
            with urllib.request.urlopen(points_url, timeout=10) as response:
                points_data = json.loads(response.read().decode())
        except urllib.error.URLError as e:
            raise WeatherAPIError(f"Failed to connect to NWS API: {e}")
        except json.JSONDecodeError as e:
            raise WeatherAPIError(f"Failed to parse NWS points response: {e}")
        
        if 'properties' not in points_data:
            raise WeatherAPIError("Invalid response from NWS points API")
        
        properties = points_data['properties']
        forecast_url = properties.get('forecast')
        
        if not forecast_url:
            raise WeatherAPIError("No forecast URL available for this location")
        
        # Get the actual forecast
        try:
            with urllib.request.urlopen(forecast_url, timeout=10) as response:
                forecast_data = json.loads(response.read().decode())
        except urllib.error.URLError as e:
            raise WeatherAPIError(f"Failed to get forecast data: {e}")
        except json.JSONDecodeError as e:
            raise WeatherAPIError(f"Failed to parse forecast response: {e}")
        
        return {
            'location': properties.get('relativeLocation', {}).get('properties', {}),
            'forecast': forecast_data.get('properties', {})
        }
    
    def format_weather_output(self, weather_data: Dict[str, Any]) -> str:
        """
        Format weather data for display.
        
        Args:
            weather_data: Weather data dictionary
            
        Returns:
            Formatted string for display
        """
        location = weather_data['location']
        forecast = weather_data['forecast']
        
        location_name = location.get('city', 'Unknown')
        state = location.get('state', '')
        if state:
            location_name += f", {state}"
        
        periods = forecast.get('periods', [])
        if not periods:
            return f"Location: {location_name}\nNo forecast data available"
        
        current_period = periods[0]
        
        output = f"Location: {location_name}\n"
        output += f"Forecast: {current_period.get('name', 'Current')}\n"
        output += f"Temperature: {current_period.get('temperature', 'Unknown')}°{current_period.get('temperatureUnit', 'F')}\n"
        output += f"Summary: {current_period.get('shortForecast', 'No summary available')}\n"
        output += f"Details: {current_period.get('detailedForecast', 'No details available')}"
        
        return output
    
    def get_weather_for_zip(self, zip_code: str) -> str:
        """
        Main method to get weather for a ZIP code.
        
        Args:
            zip_code: US ZIP code
            
        Returns:
            Formatted weather information string
            
        Raises:
            WeatherAPIError: If any step fails
        """
        # Get coordinates from ZIP code
        latitude, longitude = self.get_coordinates_from_zip(zip_code)
        
        # Get weather data
        weather_data = self.get_weather_data(latitude, longitude)
        
        # Format and return output
        return self.format_weather_output(weather_data)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Fetch weather data for a US ZIP code")
    parser.add_argument("zip_code", help="5-digit US ZIP code")
    
    args = parser.parse_args()
    
    fetcher = WeatherFetcher()
    
    try:
        weather_info = fetcher.get_weather_for_zip(args.zip_code)
        print(weather_info)
    except WeatherAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()