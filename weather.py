#!/usr/bin/env python3
"""
Weather Data Fetcher from National Weather Service API

This script fetches current weather data for a given ZIP code using the 
National Weather Service API. It converts ZIP codes to coordinates and 
then retrieves weather information.

Usage:
    python weather.py <zip_code>

Example:
    python weather.py 90210
"""

import sys
import argparse
import requests
import json
from typing import Optional, Dict, Any


class WeatherFetcher:
    """Class to handle weather data fetching from NWS API."""
    
    def __init__(self):
        self.geocoding_base_url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        self.nws_base_url = "https://api.weather.gov"
        self.session = requests.Session()
        # Set User-Agent as required by NWS API
        self.session.headers.update({
            'User-Agent': 'WeatherFetcher/1.0 (github.com/MarcAsher/WeatherTest2)'
        })
    
    def zip_to_coordinates(self, zip_code: str) -> Optional[Dict[str, float]]:
        """
        Convert ZIP code to latitude and longitude coordinates using Census Geocoding API.
        
        Args:
            zip_code: 5-digit ZIP code string
            
        Returns:
            Dictionary with 'lat' and 'lon' keys, or None if not found
        """
        try:
            params = {
                'address': zip_code,
                'benchmark': 'Public_AR_Current',
                'format': 'json'
            }
            
            response = self.session.get(self.geocoding_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['result']['addressMatches']:
                coords = data['result']['addressMatches'][0]['coordinates']
                return {
                    'lat': float(coords['y']),
                    'lon': float(coords['x'])
                }
            else:
                return None
                
        except requests.RequestException as e:
            print(f"Error converting ZIP code to coordinates: {e}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error parsing geocoding response: {e}")
            return None
    
    def get_weather_urls(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """
        Get weather forecast URLs from NWS API points endpoint.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with forecast URLs, or None if error
        """
        try:
            points_url = f"{self.nws_base_url}/points/{lat:.4f},{lon:.4f}"
            response = self.session.get(points_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'forecast': data['properties']['forecast'],
                'forecastHourly': data['properties']['forecastHourly']
            }
            
        except requests.RequestException as e:
            print(f"Error getting weather URLs: {e}")
            return None
        except KeyError as e:
            print(f"Error parsing points response: {e}")
            return None
    
    def get_current_weather(self, forecast_url: str) -> Optional[Dict[str, Any]]:
        """
        Get current weather data from NWS forecast endpoint.
        
        Args:
            forecast_url: URL to the forecast endpoint
            
        Returns:
            Dictionary with current weather data, or None if error
        """
        try:
            response = self.session.get(forecast_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            periods = data['properties']['periods']
            
            if periods:
                current = periods[0]  # First period is current/today
                return {
                    'name': current['name'],
                    'temperature': current['temperature'],
                    'temperatureUnit': current['temperatureUnit'],
                    'windSpeed': current['windSpeed'],
                    'windDirection': current['windDirection'],
                    'shortForecast': current['shortForecast'],
                    'detailedForecast': current['detailedForecast']
                }
            else:
                return None
                
        except requests.RequestException as e:
            print(f"Error getting weather data: {e}")
            return None
        except KeyError as e:
            print(f"Error parsing weather response: {e}")
            return None
    
    def fetch_weather(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """
        Main method to fetch weather data for a given ZIP code.
        
        Args:
            zip_code: 5-digit ZIP code string
            
        Returns:
            Dictionary with weather data, or None if error
        """
        # Validate ZIP code format
        if not zip_code.isdigit() or len(zip_code) != 5:
            print(f"Error: Invalid ZIP code format '{zip_code}'. Please enter a 5-digit ZIP code.")
            return None
        
        print(f"Fetching weather data for ZIP code: {zip_code}")
        
        # Step 1: Convert ZIP to coordinates
        coords = self.zip_to_coordinates(zip_code)
        if not coords:
            print(f"Error: Could not find coordinates for ZIP code {zip_code}")
            return None
        
        print(f"Found coordinates: {coords['lat']:.4f}, {coords['lon']:.4f}")
        
        # Step 2: Get weather forecast URLs
        urls = self.get_weather_urls(coords['lat'], coords['lon'])
        if not urls:
            print("Error: Could not get weather forecast URLs")
            return None
        
        # Step 3: Get current weather data
        weather_data = self.get_current_weather(urls['forecast'])
        if not weather_data:
            print("Error: Could not get current weather data")
            return None
        
        # Add location info to weather data
        weather_data['zip_code'] = zip_code
        weather_data['coordinates'] = coords
        
        return weather_data


def display_weather(weather_data: Dict[str, Any]) -> None:
    """
    Display weather data in a readable format.
    
    Args:
        weather_data: Dictionary containing weather information
    """
    print("\n" + "="*50)
    print(f"WEATHER DATA FOR ZIP CODE: {weather_data['zip_code']}")
    print("="*50)
    print(f"Location: {weather_data['coordinates']['lat']:.4f}, {weather_data['coordinates']['lon']:.4f}")
    print(f"Period: {weather_data['name']}")
    print(f"Temperature: {weather_data['temperature']}°{weather_data['temperatureUnit']}")
    print(f"Conditions: {weather_data['shortForecast']}")
    print(f"Wind: {weather_data['windSpeed']} {weather_data['windDirection']}")
    print(f"\nDetailed Forecast:")
    print(f"{weather_data['detailedForecast']}")
    print("="*50)


def main():
    """Main function to handle command line arguments and fetch weather data."""
    parser = argparse.ArgumentParser(
        description="Fetch weather data from National Weather Service API using ZIP code"
    )
    parser.add_argument(
        "zip_code",
        help="5-digit ZIP code (e.g., 90210)"
    )
    
    args = parser.parse_args()
    
    try:
        weather_fetcher = WeatherFetcher()
        weather_data = weather_fetcher.fetch_weather(args.zip_code)
        
        if weather_data:
            display_weather(weather_data)
            return 0
        else:
            print("Failed to fetch weather data. Please check your ZIP code and try again.")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())