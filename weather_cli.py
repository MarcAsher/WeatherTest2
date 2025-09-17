#!/usr/bin/env python3
"""
Weather CLI Application

A command line tool to fetch weather data from the National Weather Service
given a ZIP code as an argument.

Usage:
    python weather_cli.py <ZIP_CODE>

Example:
    python weather_cli.py 10001
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from typing import Dict, Any, Optional


class WeatherError(Exception):
    """Custom exception for weather-related errors."""
    pass


class WeatherFetcher:
    """Handles fetching weather data from the National Weather Service."""
    
    ZIP_API_BASE = "https://api.zippopotam.us/us"
    NWS_API_BASE = "https://api.weather.gov"
    
    def __init__(self):
        """Initialize the WeatherFetcher."""
        pass
    
    def get_coordinates_from_zip(self, zip_code: str) -> tuple[float, float]:
        """
        Convert ZIP code to latitude and longitude coordinates.
        
        Args:
            zip_code: 5-digit ZIP code string
            
        Returns:
            Tuple of (latitude, longitude)
            
        Raises:
            WeatherError: If ZIP code is invalid or lookup fails
        """
        if not zip_code.isdigit() or len(zip_code) != 5:
            raise WeatherError(f"Invalid ZIP code format: {zip_code}")
        
        url = f"{self.ZIP_API_BASE}/{zip_code}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if 'places' not in data or not data['places']:
                raise WeatherError(f"ZIP code not found: {zip_code}")
                
            place = data['places'][0]
            lat = float(place['latitude'])
            lon = float(place['longitude'])
            
            return lat, lon
            
        except urllib.error.URLError as e:
            raise WeatherError(f"Failed to lookup ZIP code: {e}")
        except (KeyError, ValueError, IndexError) as e:
            raise WeatherError(f"Invalid response format from ZIP API: {e}")
    
    def get_weather_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetch weather data from National Weather Service.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary containing weather forecast data
            
        Raises:
            WeatherError: If weather data fetch fails
        """
        # First, get the grid point information
        points_url = f"{self.NWS_API_BASE}/points/{latitude},{longitude}"
        
        try:
            with urllib.request.urlopen(points_url) as response:
                points_data = json.loads(response.read().decode('utf-8'))
                
            properties = points_data.get('properties', {})
            forecast_url = properties.get('forecast')
            
            if not forecast_url:
                raise WeatherError("No forecast URL found in NWS response")
                
            # Now get the actual forecast
            with urllib.request.urlopen(forecast_url) as response:
                forecast_data = json.loads(response.read().decode('utf-8'))
                
            return forecast_data
            
        except urllib.error.URLError as e:
            raise WeatherError(f"Failed to fetch weather data: {e}")
        except (KeyError, ValueError) as e:
            raise WeatherError(f"Invalid response format from NWS API: {e}")
    
    def format_weather_output(self, weather_data: Dict[str, Any], zip_code: str) -> str:
        """
        Format weather data for display.
        
        Args:
            weather_data: Raw weather data from NWS API
            zip_code: Original ZIP code for reference
            
        Returns:
            Formatted weather information string
        """
        try:
            properties = weather_data.get('properties', {})
            periods = properties.get('periods', [])
            
            if not periods:
                return f"No weather data available for ZIP code {zip_code}"
            
            output = [f"Weather Forecast for ZIP Code: {zip_code}"]
            output.append("=" * 50)
            
            # Show first few periods (current and next few forecasts)
            for i, period in enumerate(periods[:3]):
                output.append(f"\n{period.get('name', 'Unknown Period')}:")
                output.append(f"  Temperature: {period.get('temperature', 'N/A')}°{period.get('temperatureUnit', 'F')}")
                output.append(f"  Conditions: {period.get('shortForecast', 'N/A')}")
                output.append(f"  Wind: {period.get('windSpeed', 'N/A')} {period.get('windDirection', '')}")
                
                detailed = period.get('detailedForecast', '')
                if detailed:
                    output.append(f"  Details: {detailed}")
            
            return "\n".join(output)
            
        except (KeyError, TypeError) as e:
            return f"Error formatting weather data: {e}"


def main():
    """Main entry point for the weather CLI application."""
    parser = argparse.ArgumentParser(
        description="Fetch weather data from National Weather Service by ZIP code",
        epilog="Example: python weather_cli.py 10001"
    )
    parser.add_argument(
        "zip_code", 
        help="5-digit ZIP code to get weather for"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    weather_fetcher = WeatherFetcher()
    
    try:
        if args.verbose:
            print(f"Looking up coordinates for ZIP code: {args.zip_code}")
            
        # Get coordinates from ZIP code
        lat, lon = weather_fetcher.get_coordinates_from_zip(args.zip_code)
        
        if args.verbose:
            print(f"Found coordinates: {lat}, {lon}")
            print("Fetching weather data...")
            
        # Get weather data
        weather_data = weather_fetcher.get_weather_data(lat, lon)
        
        # Format and display results
        output = weather_fetcher.format_weather_output(weather_data, args.zip_code)
        print(output)
        
    except WeatherError as e:
        print(f"Weather Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()