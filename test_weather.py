#!/usr/bin/env python3
"""
Automated Testing Script for Weather CLI Application

This script tests the weather CLI application with various scenarios including
valid ZIP codes, invalid inputs, and edge cases.

Usage:
    python test_weather.py

Features:
- Unit tests for WeatherFetcher class
- Integration tests with mock data
- Error handling tests
- Command line interface tests
"""

import unittest
import sys
import os
import json
import tempfile
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

# Add the current directory to path to import weather_cli
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weather_cli import WeatherFetcher, WeatherError, main


class TestWeatherFetcher(unittest.TestCase):
    """Test cases for the WeatherFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.weather_fetcher = WeatherFetcher()
        
        # Sample mock data for testing
        self.mock_zip_response = {
            "post code": "10001",
            "country": "United States",
            "country abbreviation": "US",
            "places": [
                {
                    "place name": "New York",
                    "longitude": "-73.9851",
                    "state": "New York",
                    "state abbreviation": "NY",
                    "latitude": "40.7589"
                }
            ]
        }
        
        self.mock_nws_points_response = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/OKX/32,34/forecast",
                "forecastHourly": "https://api.weather.gov/gridpoints/OKX/32,34/forecast/hourly",
                "gridId": "OKX",
                "gridX": 32,
                "gridY": 34
            }
        }
        
        self.mock_nws_forecast_response = {
            "properties": {
                "periods": [
                    {
                        "number": 1,
                        "name": "Today",
                        "temperature": 72,
                        "temperatureUnit": "F",
                        "windSpeed": "5 mph",
                        "windDirection": "SW",
                        "shortForecast": "Partly Cloudy",
                        "detailedForecast": "Partly cloudy with a high near 72."
                    },
                    {
                        "number": 2,
                        "name": "Tonight",
                        "temperature": 58,
                        "temperatureUnit": "F",
                        "windSpeed": "3 mph",
                        "windDirection": "W",
                        "shortForecast": "Clear",
                        "detailedForecast": "Clear skies with a low around 58."
                    }
                ]
            }
        }
    
    def test_validate_zip_code_valid(self):
        """Test that valid ZIP codes are accepted."""
        # This will fail without network, but tests the validation logic
        with self.assertRaises(WeatherError):
            # Should fail on network, not validation
            self.weather_fetcher.get_coordinates_from_zip("10001")
    
    def test_validate_zip_code_invalid_format(self):
        """Test that invalid ZIP code formats are rejected."""
        invalid_zips = ["1234", "123456", "abcde", "12a34", ""]
        
        for invalid_zip in invalid_zips:
            with self.assertRaises(WeatherError) as context:
                self.weather_fetcher.get_coordinates_from_zip(invalid_zip)
            self.assertIn("Invalid ZIP code format", str(context.exception))
    
    @patch('urllib.request.urlopen')
    def test_get_coordinates_from_zip_success(self, mock_urlopen):
        """Test successful ZIP code to coordinates conversion."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(self.mock_zip_response).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        lat, lon = self.weather_fetcher.get_coordinates_from_zip("10001")
        
        self.assertEqual(lat, 40.7589)
        self.assertEqual(lon, -73.9851)
    
    @patch('urllib.request.urlopen')
    def test_get_coordinates_from_zip_not_found(self, mock_urlopen):
        """Test ZIP code not found scenario."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"places": []}).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        with self.assertRaises(WeatherError) as context:
            self.weather_fetcher.get_coordinates_from_zip("99999")
        self.assertIn("ZIP code not found", str(context.exception))
    
    @patch('urllib.request.urlopen')
    def test_get_weather_data_success(self, mock_urlopen):
        """Test successful weather data retrieval."""
        # Mock the two API calls (points and forecast)
        points_response = MagicMock()
        points_response.read.return_value = json.dumps(self.mock_nws_points_response).encode('utf-8')
        points_response.__enter__.return_value = points_response
        
        forecast_response = MagicMock()
        forecast_response.read.return_value = json.dumps(self.mock_nws_forecast_response).encode('utf-8')
        forecast_response.__enter__.return_value = forecast_response
        
        mock_urlopen.side_effect = [points_response, forecast_response]
        
        weather_data = self.weather_fetcher.get_weather_data(40.7589, -73.9851)
        
        self.assertIn('properties', weather_data)
        self.assertIn('periods', weather_data['properties'])
        self.assertEqual(len(weather_data['properties']['periods']), 2)
    
    def test_format_weather_output(self):
        """Test weather data formatting."""
        output = self.weather_fetcher.format_weather_output(self.mock_nws_forecast_response, "10001")
        
        self.assertIn("Weather Forecast for ZIP Code: 10001", output)
        self.assertIn("Today:", output)
        self.assertIn("Temperature: 72°F", output)
        self.assertIn("Partly Cloudy", output)
        self.assertIn("Tonight:", output)
    
    def test_format_weather_output_empty_data(self):
        """Test weather data formatting with empty data."""
        empty_data = {"properties": {"periods": []}}
        output = self.weather_fetcher.format_weather_output(empty_data, "10001")
        
        self.assertIn("No weather data available", output)


class TestCommandLineInterface(unittest.TestCase):
    """Test cases for the command line interface."""
    
    def test_cli_help(self):
        """Test that help message is displayed."""
        result = subprocess.run(
            [sys.executable, "weather_cli.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("Fetch weather data", result.stdout)
        self.assertIn("5-digit ZIP code", result.stdout)
    
    def test_cli_no_arguments(self):
        """Test CLI behavior with no arguments."""
        result = subprocess.run(
            [sys.executable, "weather_cli.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required", result.stderr.lower())
    
    def test_cli_invalid_zip(self):
        """Test CLI behavior with invalid ZIP code."""
        result = subprocess.run(
            [sys.executable, "weather_cli.py", "invalid"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Weather Error", result.stderr)


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.weather_fetcher = WeatherFetcher()
    
    def test_weather_error_inheritance(self):
        """Test that WeatherError is properly inherited from Exception."""
        error = WeatherError("Test error")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "Test error")
    
    @patch('urllib.request.urlopen')
    def test_network_error_handling(self, mock_urlopen):
        """Test handling of network errors."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Network error")
        
        with self.assertRaises(WeatherError):
            self.weather_fetcher.get_coordinates_from_zip("10001")


class TestIntegration(unittest.TestCase):
    """Integration tests for the entire application."""
    
    @patch('weather_cli.WeatherFetcher.get_coordinates_from_zip')
    @patch('weather_cli.WeatherFetcher.get_weather_data')
    def test_main_function_success(self, mock_get_weather, mock_get_coords):
        """Test the main function with mocked external calls."""
        mock_get_coords.return_value = (40.7589, -73.9851)
        mock_get_weather.return_value = {
            "properties": {
                "periods": [{
                    "name": "Today",
                    "temperature": 72,
                    "temperatureUnit": "F",
                    "shortForecast": "Sunny",
                    "windSpeed": "5 mph",
                    "windDirection": "W",
                    "detailedForecast": "Sunny skies"
                }]
            }
        }
        
        # Redirect stdout to capture output
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('sys.argv', ['weather_cli.py', '10001']):
                main()
                
        output = mock_stdout.getvalue()
        self.assertIn("Weather Forecast for ZIP Code: 10001", output)
        self.assertIn("Today:", output)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestWeatherFetcher,
        TestCommandLineInterface, 
        TestErrorHandling,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors))/result.testsRun*100:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running automated tests for Weather CLI Application...")
    print("="*50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)