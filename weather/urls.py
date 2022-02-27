from django.urls import path

from weather.views import WeatherInfoApi

urlpatterns = [
    path('weather', WeatherInfoApi.as_view())
]