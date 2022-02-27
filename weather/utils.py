import requests

import json

from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import activate
from cerberus import Validator
from rest_framework import status

from datetime import datetime


CITY = 'city'
COUNTRY = 'country'

LATITUDE = 'lat'
LONGITUDE = 'lon'

WEATHER_SERVICE_PARAMS = (
    CITY,
    COUNTRY
)

FORECAST_SERVICE_PARAMS = (
    LATITUDE,
    LONGITUDE,
)

def get_or_set_cache(key, func, time):
    cached_info = cache.get(key)
    if cached_info is not None:
        return cached_info
    value = func(*key)
    cache.set(key, value, time)
    return value

def get_weather_data(city, country):
    """ Returns the weather data.

    Parameters
    ----------

    city: str
        City name

    country: str
        Country code

    """
    result, code = call_third_party_weather(**{'city':city, 'country': country})
    if code != 200:
        return {'code': code, 'detail': result}
    
    return normalize_third_party_weather(result)


def call_third_party_weather(**kwargs):
    """ Calls external resources for weather.

    Parameters
    ----------

    service: str
        Name of the service

    kwargs: dict
        key to value arguments for the service

    """
    validator = Validator({
        CITY: {"required": True, "type": "string", "regex": "[A-Za-z]+"},
        COUNTRY: {"required": True, "type": "string", 
            "regex": "[a-z]+", "maxlength":2}
    })

    if not validator.validate(kwargs):
        return {
            'code': 'bad_request',
            'detail': "Invalid parameters.",
            'error': validator.errors
        }, status.HTTP_400_BAD_REQUEST

    third_party_url = (f"{settings.OPEN_WEATHER_MAP_URL}/weather?q={kwargs[CITY]},"
        f"{kwargs[COUNTRY]}&appid={settings.OPEN_WEATHER_MAP_ID}&units=metric")
    response = requests.get(url=third_party_url)
    
    if response.status_code != status.HTTP_200_OK:
        return {
            'code': 'request_error',
            'detail': "Request got an error",
            'error': response.json()
        }, response.status_code

    return response.json(), response.status_code

def call_third_party_forecast(**kwargs):
    """ Calls external resources for forecast.

    Parameters
    ----------

    kwargs: dict
        key to value arguments for the service

    """
    validator = Validator({
        LATITUDE: {"required": True, "type": "float"},
        LONGITUDE: {"required": True, "type": "float"}
    })

    if not validator.validate(kwargs):
        return {
            'code': 'bad_request',
            'detail': "Invalid parameters.",
            'error': validator.errors
        }, status.HTTP_400_BAD_REQUEST

    third_party_url = (f"{settings.OPEN_WEATHER_MAP_URL}/forecast?lat={kwargs[LATITUDE]}"
        f"&lon={kwargs[LONGITUDE]}&appid={settings.OPEN_WEATHER_MAP_ID}&units=metric")
    response = requests.get(url=third_party_url)

    if response.status_code != status.HTTP_200_OK:
        return {
            'code': 'request_error',
            'detail': "Request got an error",
            'error': response.json()
        }, response.status_code
    return response.json(), response.status_code

def normalize_third_party_weather(data:dict):
    """ Returns human readeable information from third party weather services.

    Parameters
    ----------

    data: dict
        Data to be normalized
    
    Returns
    -------

    Dict | None
        Dictionary with normalized data
        Service unavailable

    """
    location_name = f"{data.get('name', '')}, {data.get('sys', {}).get('country', '')}"

    temperature = [
        f"{round(float(data.get('main', {}).get('temp', None)))} °C",
        f"{round(float(data.get('main', {}).get('temp', None)) * 9/5 + 32)} °F"
    ]

    wind = get_wind_name_by_values(
        float(data.get('wind', {}).get('speed', 0)), 
        float(data.get('wind', {}).get('deg', 0))
    )

    cloudiness = ''
    if data.get('weather'):
        for element in data.get('weather'):
            cloudiness = element.get('description', '').capitalize()
    if cloudiness == '':
        cloudiness = get_cloudiness_by_percentage(
            float(data.get('clouds', {}).get('all', 0)))

    sunrise = datetime.fromtimestamp(
        data.get('sys', {}).get('sunrise', ''), activate(settings.TIME_ZONE)
    ).strftime('%H:%M')

    sunset = datetime.fromtimestamp(
        data.get('sys', {}).get('sunset', ''), activate(settings.TIME_ZONE)
    ).strftime('%H:%M')

    geo_coordinates = [
        data.get('coord', {}).get('lat', None),
        data.get('coord', {}).get('lon', None),
    ]

    pressure = f"{data.get('main', {}).get('pressure', 0)} hpa"

    humidity = f"{round(data.get('main', {}).get('humidity', 0))}%"

    requested_time = datetime.fromtimestamp(
        data.get('dt', 0), activate(settings.TIME_ZONE)
    ).strftime('%m/%d/%Y, %H:%M:%S')

    forecast, code = call_third_party_forecast(**{
        'lat': float(geo_coordinates[0]),
        'lon': float(geo_coordinates[1])
    })

    if code != 200:
        forecast = "Service not available."

    return {
        'location_name': location_name,
        'temperature': temperature,
        'wind': wind,
        'cloudiness': cloudiness,
        'pressure': pressure,
        'humidity': humidity,
        'sunrise': sunrise,
        'sunset': sunset,
        'geo_coordinates': geo_coordinates,
        'requested_time': requested_time,
        'forecast': forecast if code != 200 
            else normalize_third_party_forecast(forecast),
    }

def normalize_third_party_forecast(data:dict):
    """ Returns human readeable information from third party forecast services.

    Parameters
    ----------

    data: dict
        Data to be normalized
    
    Returns
    -------

    Dict | None
        Dictionary with normalized data
        Service unavailable

    """
    total_forecasts = data.get('cnt', '')

    forecast_data = []
    for forecast_read in data.get('list', ''):
        temperature = [
            f"{round(float(forecast_read.get('main', {}).get('temp', None)))} °C",
            f"{round(float(forecast_read.get('main', {}).get('temp', None)) * 9/5 + 32)} °F"
        ]

        wind = get_wind_name_by_values(
            float(forecast_read.get('wind', {}).get('speed', 0)), 
            float(forecast_read.get('wind', {}).get('deg', 0))
        )

        cloudiness = get_cloudiness_by_percentage(
            float(forecast_read.get('clouds', {}).get('all', 0)))

        precipitation = f"{round(forecast_read.get('pop', 0) * 100)}%"

        pressure = f"{forecast_read.get('main', {}).get('pressure', 0)} hpa"

        humidity = f"{round(forecast_read.get('main', {}).get('humidity', 0))}%"

        time_forecasted = datetime.fromtimestamp(
            forecast_read.get('dt', 0), activate(settings.TIME_ZONE)
        ).strftime('%m/%d/%Y, %H:%M:%S')

        forecast_data.append({
            'temperature': temperature,
            'wind': wind,
            'cloudiness': cloudiness,
            'precipitation': precipitation,
            'pressure': pressure,
            'humidity': humidity,
            'time_forecasted': time_forecasted
        })
    
    return {
        'total_forecasts': total_forecasts,
        'forecast_data': forecast_data
    }

def get_wind_name_by_values(speed:float, deg:float):
    """Returns the readeable name for wind speed and degrees

    Parameters
    ----------

    speed: float
        Wind speed in m/s

    deg: float
        Wind direction in degrees
    
    Returns
    -------

    String
        Readeable wind name

    """
    speed_name = ''
    deg_name = ''
    speed_names = {
        "Calm":0, 
        "Light Air":1.5, 
        "Light Breeze":3.3, 
        "Gentle Breeze":5.4, 
        "Moderate Breeze":7.9, 
        "Fresh Breeze":8.0, 
        "Strong Breeze":13.8, 
        "Near Gale":17.1, 
        "Gale":20.7, 
        "Severe Gale":24.4, 
        "Strong storm":28.4, 
        "Violent Storm":32.6, 
        "Hurricane":32.7
    }
    deg_names = {
        "North":0,
        "North-Northeast":22.5,
        "Northeast":45,
        "East-Northeast":67.5,
        "East":90,
        "East-Southeast":112.5,
        "Southeast":135, 
        "South-Southeast":157.5,
        "South":180,
        "South-Southwest":202.5,
        "Southwest":225,
        "West-Southwest":247.5,
        "West":270,
        "West-Northwest":292.5,
        "Northwest":315,
        "North-Northwest":337.5
    }
    for key, value in speed_names.items():
        if speed >= value:
            speed_name = key
    for key, value in deg_names.items():
        if deg >= value:
            deg_name = key
    return f"{speed_name}, {speed} m/s, {deg_name}"

def get_cloudiness_by_percentage(percentage:float):
    """Returns the type of cloudiness by percentage using okta scale

    Parameters
    ----------

    percentage: float
        Cloudiness percentage
    
    Returns
    -------

    String
        Readeable cloudiness name

    """
    cloudiness = ''
    cloud_oktas = {
        1:0,
        2:18.75,
        3:31.25,
        4:43.75,
        5:56.25,
        6:68.75,
        7:81.25,
        8:100
    }
    oktas_to_cloudiness = {
        "Few clouds": (1, 2, 3),
        "Scattered clouds": (4, 5),
        "Broken clouds": (6, 7, 8),
    }
    if percentage == 0:
        cloudiness = "Clear sky"
    else:
        okta_value = 1
        for key, value in cloud_oktas.items():
            if percentage >= value:
                okta_value = key
        for key, value in oktas_to_cloudiness.items():
            if okta_value in value:
                cloudiness = key
    return cloudiness