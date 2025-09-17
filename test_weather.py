#!/usr/bin/env python3
"""
Test script for the weather data fetcher.

This script tests the main functionality of weather.py including:
- Valid ZIP code handling
- Invalid ZIP code handling  
- Network error handling
- API response parsing

Usage:
    python test_weather.py
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests

# Add the current directory to the path to import weather module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weather import WeatherFetcher, display_weather


class TestWeatherFetcher(unittest.TestCase):
    """Test cases for the WeatherFetcher class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.weather_fetcher = WeatherFetcher()
    
    def test_zip_code_validation(self):
        """Test ZIP code format validation."""
        # Test invalid ZIP codes
        invalid_zips = ["1234", "123456", "abcde", "12ab5", ""]
        for zip_code in invalid_zips:
            result = self.weather_fetcher.fetch_weather(zip_code)
            self.assertIsNone(result, f"Should return None for invalid ZIP: {zip_code}")
    
    def test_valid_zip_code_format(self):
        """Test that valid ZIP code formats pass initial validation."""
        valid_zip = "90210"
        # Mock the network calls to test just the validation
        with patch.object(self.weather_fetcher, 'zip_to_coordinates', return_value=None):
            result = self.weather_fetcher.fetch_weather(valid_zip)
            # Should not fail on format validation, but will fail on mocked geocoding
            # We expect None due to mocked geocoding failure, not format validation
    
    @patch('weather.requests.Session.get')
    def test_zip_to_coordinates_success(self, mock_get):
        """Test successful ZIP code to coordinates conversion."""
        # Mock successful geocoding response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'result': {
                'addressMatches': [{
                    'coordinates': {
                        'x': -118.4085,
                        'y': 34.0901
                    }
                }]
            }
        }
        mock_get.return_value = mock_response
        
        result = self.weather_fetcher.zip_to_coordinates("90210")
        
        self.assertIsNotNone(result)
        self.assertIn('lat', result)
        self.assertIn('lon', result)
        self.assertEqual(result['lat'], 34.0901)
        self.assertEqual(result['lon'], -118.4085)
    
    @patch('weather.requests.Session.get')
    def test_zip_to_coordinates_not_found(self, mock_get):
        """Test ZIP code not found in geocoding."""
        # Mock geocoding response with no matches
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'result': {
                'addressMatches': []
            }
        }
        mock_get.return_value = mock_response
        
        result = self.weather_fetcher.zip_to_coordinates("99999")
        self.assertIsNone(result)
    
    @patch('weather.requests.Session.get')
    def test_zip_to_coordinates_network_error(self, mock_get):
        """Test network error during geocoding."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        result = self.weather_fetcher.zip_to_coordinates("90210")
        self.assertIsNone(result)
    
    @patch('weather.requests.Session.get')
    def test_get_weather_urls_success(self, mock_get):
        """Test successful weather URLs retrieval."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'properties': {
                'forecast': 'https://api.weather.gov/gridpoints/LOX/123,456/forecast',
                'forecastHourly': 'https://api.weather.gov/gridpoints/LOX/123,456/forecast/hourly'
            }
        }
        mock_get.return_value = mock_response
        
        result = self.weather_fetcher.get_weather_urls(34.0901, -118.4085)
        
        self.assertIsNotNone(result)
        self.assertIn('forecast', result)
        self.assertIn('forecastHourly', result)
    
    @patch('weather.requests.Session.get')
    def test_get_weather_urls_network_error(self, mock_get):
        """Test network error during weather URLs retrieval."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        result = self.weather_fetcher.get_weather_urls(34.0901, -118.4085)
        self.assertIsNone(result)
    
    @patch('weather.requests.Session.get')
    def test_get_current_weather_success(self, mock_get):
        """Test successful current weather data retrieval."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'properties': {
                'periods': [{
                    'name': 'Today',
                    'temperature': 75,
                    'temperatureUnit': 'F',
                    'windSpeed': '10 mph',
                    'windDirection': 'SW',
                    'shortForecast': 'Sunny',
                    'detailedForecast': 'Sunny skies with light winds.'
                }]
            }
        }
        mock_get.return_value = mock_response
        
        result = self.weather_fetcher.get_current_weather('https://api.weather.gov/gridpoints/LOX/123,456/forecast')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'Today')
        self.assertEqual(result['temperature'], 75)
        self.assertEqual(result['temperatureUnit'], 'F')
        self.assertEqual(result['shortForecast'], 'Sunny')
    
    @patch('weather.requests.Session.get')
    def test_get_current_weather_no_periods(self, mock_get):
        """Test weather data retrieval with no periods."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'properties': {
                'periods': []
            }
        }
        mock_get.return_value = mock_response
        
        result = self.weather_fetcher.get_current_weather('https://api.weather.gov/gridpoints/LOX/123,456/forecast')
        self.assertIsNone(result)
    
    @patch('weather.requests.Session.get')
    def test_get_current_weather_network_error(self, mock_get):
        """Test network error during weather data retrieval."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        result = self.weather_fetcher.get_current_weather('https://api.weather.gov/gridpoints/LOX/123,456/forecast')
        self.assertIsNone(result)
    
    @patch.object(WeatherFetcher, 'get_current_weather')
    @patch.object(WeatherFetcher, 'get_weather_urls')
    @patch.object(WeatherFetcher, 'zip_to_coordinates')
    def test_fetch_weather_complete_success(self, mock_zip_to_coords, mock_get_urls, mock_get_weather):
        """Test complete successful weather fetch workflow."""
        # Mock all the method calls
        mock_zip_to_coords.return_value = {'lat': 34.0901, 'lon': -118.4085}
        mock_get_urls.return_value = {
            'forecast': 'https://api.weather.gov/gridpoints/LOX/123,456/forecast',
            'forecastHourly': 'https://api.weather.gov/gridpoints/LOX/123,456/forecast/hourly'
        }
        mock_get_weather.return_value = {
            'name': 'Today',
            'temperature': 75,
            'temperatureUnit': 'F',
            'windSpeed': '10 mph',
            'windDirection': 'SW',
            'shortForecast': 'Sunny',
            'detailedForecast': 'Sunny skies with light winds.'
        }
        
        result = self.weather_fetcher.fetch_weather("90210")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['zip_code'], "90210")
        self.assertEqual(result['temperature'], 75)
        self.assertIn('coordinates', result)
    
    @patch.object(WeatherFetcher, 'zip_to_coordinates')
    def test_fetch_weather_geocoding_failure(self, mock_zip_to_coords):
        """Test weather fetch with geocoding failure."""
        mock_zip_to_coords.return_value = None
        
        result = self.weather_fetcher.fetch_weather("90210")
        self.assertIsNone(result)
    
    @patch.object(WeatherFetcher, 'get_weather_urls')
    @patch.object(WeatherFetcher, 'zip_to_coordinates')
    def test_fetch_weather_urls_failure(self, mock_zip_to_coords, mock_get_urls):
        """Test weather fetch with weather URLs failure."""
        mock_zip_to_coords.return_value = {'lat': 34.0901, 'lon': -118.4085}
        mock_get_urls.return_value = None
        
        result = self.weather_fetcher.fetch_weather("90210")
        self.assertIsNone(result)
    
    @patch.object(WeatherFetcher, 'get_current_weather')
    @patch.object(WeatherFetcher, 'get_weather_urls')
    @patch.object(WeatherFetcher, 'zip_to_coordinates')
    def test_fetch_weather_data_failure(self, mock_zip_to_coords, mock_get_urls, mock_get_weather):
        """Test weather fetch with weather data failure."""
        mock_zip_to_coords.return_value = {'lat': 34.0901, 'lon': -118.4085}
        mock_get_urls.return_value = {
            'forecast': 'https://api.weather.gov/gridpoints/LOX/123,456/forecast'
        }
        mock_get_weather.return_value = None
        
        result = self.weather_fetcher.fetch_weather("90210")
        self.assertIsNone(result)


class TestDisplayWeather(unittest.TestCase):
    """Test cases for the display_weather function."""
    
    @patch('builtins.print')
    def test_display_weather(self, mock_print):
        """Test weather data display function."""
        weather_data = {
            'zip_code': '90210',
            'coordinates': {'lat': 34.0901, 'lon': -118.4085},
            'name': 'Today',
            'temperature': 75,
            'temperatureUnit': 'F',
            'windSpeed': '10 mph',
            'windDirection': 'SW',
            'shortForecast': 'Sunny',
            'detailedForecast': 'Sunny skies with light winds.'
        }
        
        display_weather(weather_data)
        
        # Verify that print was called (weather data was displayed)
        self.assertTrue(mock_print.called)
        
        # Check some of the printed content
        printed_calls = [call[0][0] for call in mock_print.call_args_list if call[0]]
        printed_text = ' '.join(printed_calls)
        
        self.assertIn('90210', printed_text)
        self.assertIn('75°F', printed_text)
        self.assertIn('Sunny', printed_text)


class TestIntegration(unittest.TestCase):
    """Integration tests that test the complete workflow without mocking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.weather_fetcher = WeatherFetcher()
    
    def test_invalid_zip_codes_integration(self):
        """Integration test for various invalid ZIP codes."""
        invalid_zips = ["1234", "123456", "abcde", "12ab5", "", "00000"]
        
        for zip_code in invalid_zips:
            with self.subTest(zip_code=zip_code):
                result = self.weather_fetcher.fetch_weather(zip_code)
                self.assertIsNone(result, f"Invalid ZIP {zip_code} should return None")


def run_test_suite():
    """Run the complete test suite."""
    print("Running Weather Fetcher Test Suite")
    print("=" * 50)
    
    # Create test suite using TestLoader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestWeatherFetcher))
    suite.addTest(loader.loadTestsFromTestCase(TestDisplayWeather))
    suite.addTest(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nTest suite {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)