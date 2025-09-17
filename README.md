# WeatherTest2
Test to pull weather data

## Description
This repository contains a Python script that fetches weather data from the National Weather Service (NWS) API using a ZIP code provided as a command line argument.

## Features
- Fetches current weather data using ZIP codes
- Uses the National Weather Service API for reliable weather information  
- Converts ZIP codes to coordinates using the Census Geocoding API
- Displays weather data in a readable format
- Handles errors gracefully (invalid ZIP codes, network issues, etc.)
- Includes comprehensive test suite

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MarcAsher/WeatherTest2.git
cd WeatherTest2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python weather.py <zip_code>
```

### Examples
```bash
# Get weather for Beverly Hills, CA
python weather.py 90210

# Get weather for New York, NY
python weather.py 10001

# Get weather for Seattle, WA  
python weather.py 98101
```

### Sample Output
```
Fetching weather data for ZIP code: 90210
Found coordinates: 34.0901, -118.4085

==================================================
WEATHER DATA FOR ZIP CODE: 90210
==================================================
Location: 34.0901, -118.4085
Period: Today
Temperature: 75°F
Conditions: Sunny
Wind: 10 mph SW

Detailed Forecast:
Sunny skies with light winds.
==================================================
```

## Testing

Run the test suite to validate functionality:

```bash
python test_weather.py
```

The test suite includes:
- Tests for valid ZIP code handling
- Tests for invalid ZIP code error handling
- Tests for network error handling
- Integration tests
- API response parsing tests

## Error Handling

The script handles various error conditions:
- **Invalid ZIP code format**: Shows error message for non-5-digit ZIP codes
- **ZIP code not found**: Shows error when geocoding fails to find coordinates
- **Network errors**: Handles timeouts and connection issues gracefully
- **API errors**: Handles cases where the NWS API is unavailable or returns invalid data

## API Dependencies

This script uses two external APIs:
1. **Census Geocoding API**: Converts ZIP codes to latitude/longitude coordinates
2. **National Weather Service API**: Provides weather forecast data

Both APIs are free and do not require API keys.
