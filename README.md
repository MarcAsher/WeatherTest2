# WeatherTest2
Test to pull weather data

## Weather CLI Application

A Python command line application that fetches weather data from the National Weather Service when given a ZIP code as an argument.

### Features

- Converts ZIP codes to geographic coordinates using the Zippopotamus API
- Fetches weather forecast data from the National Weather Service API
- Displays formatted weather information for the current and upcoming periods
- Comprehensive error handling for invalid inputs and network issues
- Verbose mode for debugging
- Full automated testing suite

### Usage

#### Basic Usage
```bash
python weather_cli.py <ZIP_CODE>
```

#### Examples
```bash
# Get weather for New York City
python weather_cli.py 10001

# Get weather with verbose output
python weather_cli.py 10001 --verbose

# Show help
python weather_cli.py --help
```

#### Sample Output
```
Weather Forecast for ZIP Code: 10001
==================================================

Today:
  Temperature: 72°F
  Conditions: Partly Cloudy
  Wind: 5 mph SW
  Details: Partly cloudy with a high near 72.

Tonight:
  Temperature: 58°F
  Conditions: Clear
  Wind: 3 mph W
  Details: Clear skies with a low around 58.
```

### Requirements

This application uses only Python standard library modules, so no additional dependencies are required. Python 3.7+ is recommended.

### Testing

The application includes a comprehensive automated testing suite:

```bash
# Run all tests
python test_weather.py
```

The test suite includes:
- Unit tests for the WeatherFetcher class
- Integration tests with mocked API responses
- Error handling and edge case tests
- Command line interface tests

### API Information

This application uses two external APIs:

1. **Zippopotamus API** (`api.zippopotam.us`) - Converts ZIP codes to latitude/longitude coordinates
2. **National Weather Service API** (`api.weather.gov`) - Provides weather forecast data

### Error Handling

The application handles various error scenarios:
- Invalid ZIP code formats (non-numeric, wrong length)
- ZIP codes not found in the database
- Network connectivity issues
- Invalid API responses
- Missing weather data

### Files

- `weather_cli.py` - Main command line application
- `test_weather.py` - Automated testing script  
- `requirements.txt` - Dependencies (currently none, uses standard library only)
- `README.md` - This documentation
