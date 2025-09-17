#!/usr/bin/env python3
"""
Test suite for the weather data fetcher script.
"""

import json
import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

# Add the current directory to the path so we can import weather
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weather import WeatherFetcher, WeatherAPIError, main


class TestWeatherFetcher(unittest.TestCase):
    """Test cases for WeatherFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fetcher = WeatherFetcher()
    
    def test_invalid_zip_codes(self):
        """Test that invalid ZIP codes raise appropriate errors."""
        invalid_zips = [
            "",           # Empty string
            "1234",       # Too short
            "123456",     # Too long
            "abcde",      # Non-numeric
            "12a45",      # Mixed characters
            None,         # None value
        ]
        
        for invalid_zip in invalid_zips:
            with self.subTest(zip_code=invalid_zip):
                with self.assertRaises(WeatherAPIError) as context:
                    self.fetcher.get_coordinates_from_zip(invalid_zip)
                self.assertIn("Invalid ZIP code format", str(context.exception))
    
    @patch('urllib.request.urlopen')
    def test_geocoding_success(self, mock_urlopen):
        """Test successful geocoding of ZIP code."""
        # Mock response from Census API
        mock_response_data = {
            "result": {
                "addressMatches": [{
                    "coordinates": {
                        "x": -122.4194,  # longitude
                        "y": 37.7749     # latitude
                    }
                }]
            }
        }
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        lat, lon = self.fetcher.get_coordinates_from_zip("94102")
        
        self.assertEqual(lat, 37.7749)
        self.assertEqual(lon, -122.4194)
        mock_urlopen.assert_called_once()
    
    @patch('urllib.request.urlopen')
    def test_geocoding_no_results(self, mock_urlopen):
        """Test geocoding when no results are found."""
        mock_response_data = {
            "result": {
                "addressMatches": []
            }
        }
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        with self.assertRaises(WeatherAPIError) as context:
            self.fetcher.get_coordinates_from_zip("99999")
        
        self.assertIn("ZIP code not found", str(context.exception))
    
    @patch('urllib.request.urlopen')
    def test_geocoding_network_error(self, mock_urlopen):
        """Test geocoding when network error occurs."""
        from urllib.error import URLError
        
        mock_urlopen.side_effect = URLError("Network error")
        
        with self.assertRaises(WeatherAPIError) as context:
            self.fetcher.get_coordinates_from_zip("12345")
        
        self.assertIn("Failed to connect to geocoding service", str(context.exception))
    
    @patch('urllib.request.urlopen')
    def test_weather_api_success(self, mock_urlopen):
        """Test successful weather API calls."""
        # Mock response from points API
        points_response_data = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/MTR/90,69/forecast",
                "relativeLocation": {
                    "properties": {
                        "city": "San Francisco",
                        "state": "CA"
                    }
                }
            }
        }
        
        # Mock response from forecast API
        forecast_response_data = {
            "properties": {
                "periods": [{
                    "name": "Today",
                    "temperature": 68,
                    "temperatureUnit": "F",
                    "shortForecast": "Partly Cloudy",
                    "detailedForecast": "Partly cloudy skies with mild temperatures."
                }]
            }
        }
        
        def mock_response_side_effect(url, timeout=None):
            mock_response = MagicMock()
            if "/points/" in url and "/gridpoints/" not in url:
                mock_response.read.return_value = json.dumps(points_response_data).encode()
            elif "/gridpoints/" in url and "/forecast" in url:
                mock_response.read.return_value = json.dumps(forecast_response_data).encode()
            mock_response.__enter__.return_value = mock_response
            return mock_response
        
        mock_urlopen.side_effect = mock_response_side_effect
        
        weather_data = self.fetcher.get_weather_data(37.7749, -122.4194)
        
        self.assertIn('location', weather_data)
        self.assertIn('forecast', weather_data)
        self.assertEqual(weather_data['location']['city'], 'San Francisco')
        self.assertEqual(len(weather_data['forecast'].get('periods', [])), 1)
    
    @patch('urllib.request.urlopen')
    def test_weather_api_invalid_location(self, mock_urlopen):
        """Test weather API with invalid location coordinates."""
        # Mock response with no properties (invalid location)
        mock_response_data = {}
        
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        with self.assertRaises(WeatherAPIError) as context:
            self.fetcher.get_weather_data(999, 999)
        
        self.assertIn("Invalid response from NWS points API", str(context.exception))
    
    def test_format_weather_output(self):
        """Test weather output formatting."""
        weather_data = {
            'location': {
                'city': 'San Francisco',
                'state': 'CA'
            },
            'forecast': {
                'periods': [{
                    'name': 'Today',
                    'temperature': 68,
                    'temperatureUnit': 'F',
                    'shortForecast': 'Partly Cloudy',
                    'detailedForecast': 'Partly cloudy skies with mild temperatures.'
                }]
            }
        }
        
        output = self.fetcher.format_weather_output(weather_data)
        
        self.assertIn('Location: San Francisco, CA', output)
        self.assertIn('Temperature: 68°F', output)
        self.assertIn('Summary: Partly Cloudy', output)
        self.assertIn('Details: Partly cloudy skies with mild temperatures.', output)
    
    def test_format_weather_output_no_forecast(self):
        """Test weather output formatting when no forecast is available."""
        weather_data = {
            'location': {
                'city': 'Unknown City',
                'state': 'XX'
            },
            'forecast': {
                'periods': []
            }
        }
        
        output = self.fetcher.format_weather_output(weather_data)
        
        self.assertIn('Location: Unknown City, XX', output)
        self.assertIn('No forecast data available', output)
    
    @patch('urllib.request.urlopen')
    def test_get_weather_for_zip_integration(self, mock_urlopen):
        """Test the complete integration from ZIP code to weather output."""
        # Mock geocoding response
        geocoding_response = {
            "result": {
                "addressMatches": [{
                    "coordinates": {
                        "x": -122.4194,
                        "y": 37.7749
                    }
                }]
            }
        }
        
        # Mock points response
        points_response = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/MTR/90,69/forecast",
                "relativeLocation": {
                    "properties": {
                        "city": "San Francisco",
                        "state": "CA"
                    }
                }
            }
        }
        
        # Mock forecast response
        forecast_response = {
            "properties": {
                "periods": [{
                    "name": "Today",
                    "temperature": 68,
                    "temperatureUnit": "F",
                    "shortForecast": "Partly Cloudy",
                    "detailedForecast": "Partly cloudy skies with mild temperatures."
                }]
            }
        }
        
        def mock_response_side_effect(url, timeout=None):
            mock_response = MagicMock()
            if "geocoding.geo.census.gov" in url:
                mock_response.read.return_value = json.dumps(geocoding_response).encode()
            elif "/points/" in url and "/gridpoints/" not in url:
                mock_response.read.return_value = json.dumps(points_response).encode()
            elif "/gridpoints/" in url and "/forecast" in url:
                mock_response.read.return_value = json.dumps(forecast_response).encode()
            mock_response.__enter__.return_value = mock_response
            return mock_response
        
        mock_urlopen.side_effect = mock_response_side_effect
        
        result = self.fetcher.get_weather_for_zip("94102")
        
        self.assertIn('Location: San Francisco, CA', result)
        self.assertIn('Temperature: 68°F', result)
        self.assertIn('Summary: Partly Cloudy', result)
        # Verify that all three API calls were made (geocoding, points, forecast)
        self.assertEqual(mock_urlopen.call_count, 3)


class TestMainFunction(unittest.TestCase):
    """Test cases for the main function."""
    
    @patch('sys.argv', ['weather.py', '12345'])
    @patch('weather.WeatherFetcher.get_weather_for_zip')
    @patch('builtins.print')
    def test_main_success(self, mock_print, mock_get_weather):
        """Test successful execution of main function."""
        mock_get_weather.return_value = "Weather info for ZIP 12345"
        
        main()
        
        mock_get_weather.assert_called_once_with('12345')
        mock_print.assert_called_once_with("Weather info for ZIP 12345")
    
    @patch('sys.argv', ['weather.py', 'invalid'])
    @patch('weather.WeatherFetcher.get_weather_for_zip')
    @patch('builtins.print')
    @patch('sys.exit')
    def test_main_weather_api_error(self, mock_exit, mock_print, mock_get_weather):
        """Test main function handling WeatherAPIError."""
        mock_get_weather.side_effect = WeatherAPIError("Invalid ZIP code")
        
        main()
        
        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        self.assertIn("Error: Invalid ZIP code", args[0])
        self.assertEqual(kwargs.get('file'), sys.stderr)
        mock_exit.assert_called_once_with(1)
    
    @patch('sys.argv', ['weather.py', '12345'])
    @patch('weather.WeatherFetcher.get_weather_for_zip')
    @patch('builtins.print')
    @patch('sys.exit')
    def test_main_unexpected_error(self, mock_exit, mock_print, mock_get_weather):
        """Test main function handling unexpected errors."""
        mock_get_weather.side_effect = Exception("Unexpected error")
        
        main()
        
        mock_print.assert_called_once()
        args, kwargs = mock_print.call_args
        self.assertIn("Unexpected error:", args[0])
        self.assertEqual(kwargs.get('file'), sys.stderr)
        mock_exit.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()