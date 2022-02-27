from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from django.conf import settings

from .utils import get_or_set_cache, get_weather_data


class WeatherInfoApi(APIView):
    """ Defines the HTTP verbs for weather info api """

    def get(self, request):
        """ Retrieves the weather information from third party sources.

        Parameters
        ----------

        request (dict)
            Contains http transaction information.

        Returns
        -------
            Response (JSON, int)
                Body response and status code.

        """
        weather_data = get_or_set_cache(
            (request.GET.get('city'), request.GET.get('country')),
            get_weather_data,
            settings.WEATHER_DATA_CACHE_TIME
        )
        if weather_data is None:
            return Response({
                'code': 'service_unavailable',
                'detail': f"The requested service isn't available."
            }, status=status.HTTP_404_NOT_FOUND)
        return Response(weather_data, status=status.HTTP_200_OK)