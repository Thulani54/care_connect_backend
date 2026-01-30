from django.urls import re_path
from . import consumers
from drivers import consumers as driver_consumers

websocket_urlpatterns = [
    re_path(r'ws/ride/(?P<ride_id>\w+)/$', consumers.RideMatchingConsumer.as_asgi()),
    re_path(r'ws/driver/(?P<driver_id>[\w\+]+)/$', driver_consumers.DriverConsumer.as_asgi()),
]
