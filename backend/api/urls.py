from django.urls import include, path

from .v1.urls import urlpatterns

urlpatterns = [
    path("", include(urlpatterns)),
]
