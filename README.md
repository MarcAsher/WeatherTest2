# WeatherTest2
Test to pull weather data

## Weather Data Fetcher

This repository contains a Python script that fetches current weather data from the National Weather Service for a given ZIP code.

### Features

- Accepts a U.S. ZIP code as a command line argument
- Uses the US Census Bureau API to convert ZIP codes to latitude/longitude coordinates
- Retrieves current weather forecast from the National Weather Service API
- Displays location name, forecast summary, and temperature
- Handles errors gracefully (invalid ZIP codes, API errors, network issues)

### Usage

```bash
python3 weather.py <ZIP_CODE>
```

Example:
```bash
python3 weather.py 10001
```

### Requirements

The script uses only Python standard library modules, so no additional dependencies are required for the main functionality.

For running tests:
```bash
pip3 install -r requirements.txt
```

### Testing

Run the test suite:
```bash
python3 -m unittest test_weather.py -v
```

The tests include:
- Mocked network/API requests
- Testing valid and invalid ZIP codes
- Verifying correct error handling and output formatting
- Integration testing of the complete workflow

### API Documentation

The script uses:
1. **US Census Bureau Geocoding API** - Converts ZIP codes to coordinates
2. **National Weather Service API** - Retrieves weather forecasts

Both APIs are free and do not require API keys.
