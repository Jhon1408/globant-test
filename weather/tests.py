from http import client
import pytest
import json

from unittest.mock import Mock, patch
from django.core.cache import cache

from weather.utils import (
    call_third_party_weather, normalize_third_party_weather, 
    call_third_party_forecast, normalize_third_party_forecast,
    get_or_set_cache
)

CALL_THIRD_PARTY_FORECAST = 'weather/mocks/call_third_party_forecast.json'
CALL_THIRD_PARTY_WEATHER = 'weather/mocks/call_third_party_weather.json'
NORMALIZE_THIRD_PARTY_FORECAST = 'weather/mocks/normalize_third_party_data_forecast.json'
NORMALIZE_THIRD_PARTY_WEATHER = 'weather/mocks/normalize_third_party_data_weather.json'

def load_file_into_json(filename):
    return json.load(open(filename))

def create_resquest_mock(json_file, status_code=200):
    return Mock(
        data=load_file_into_json(json_file),
        status_code=status_code
    )

def mocked_request_forecast_service(*args, **kwargs):
    forecast_service_mock_response = create_resquest_mock(CALL_THIRD_PARTY_FORECAST)
    forecast_service_mock_response.json.return_value = forecast_service_mock_response.data
    return forecast_service_mock_response

def mocked_request_weather_service(*args, **kwargs):
    weather_service_mock_response = create_resquest_mock(CALL_THIRD_PARTY_WEATHER)
    weather_service_mock_response.json.return_value = weather_service_mock_response.data
    return weather_service_mock_response

class TestUtils:
    @patch('requests.get', side_effect=mocked_request_forecast_service)
    def test_call_third_party_forecast(self, mocked_request_forecast_service):
        result, status_code = call_third_party_forecast(
            **{'lat': 4.6097, 'lon': -74.0817}
        )
        assert result == mocked_request_forecast_service().data
        assert status_code == mocked_request_forecast_service().status_code
        pytest.shared = mocked_request_forecast_service().data
    
    @patch('requests.get', side_effect=mocked_request_weather_service)
    def test_call_third_party_weather(self, mocked_request_weather_service):
        result, status_code = call_third_party_weather(
            **{'city': 'Bogota', 'country': 'co'}
        )
        assert result == mocked_request_weather_service().data
        assert status_code == mocked_request_weather_service().status_code
    
    def test_normalize_third_party_data_forecast(self):
        third_party_forecast_data_mock = load_file_into_json(CALL_THIRD_PARTY_FORECAST)
        result = normalize_third_party_forecast(third_party_forecast_data_mock)
        assert result == load_file_into_json(NORMALIZE_THIRD_PARTY_FORECAST)
    
    def test_normalize_third_party_data_weather(self):
        third_party_weather_data_mock = load_file_into_json(CALL_THIRD_PARTY_WEATHER)
        result = normalize_third_party_weather(third_party_weather_data_mock)
        result.pop('forecast')
        assert result == load_file_into_json(NORMALIZE_THIRD_PARTY_WEATHER)
    
    def test_get_or_set_cache(self):
        mock_function = Mock()
        mock_function.test.return_value = 1
        key = 'test'
        result = get_or_set_cache(key, mock_function.test, None)
        assert result == mock_function.test()
        assert cache.get('test') == 1