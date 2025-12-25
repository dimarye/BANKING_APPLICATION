from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def health(_request):
    return HttpResponse("OK")


urlpatterns = [
    path("", health),
    path("admin/", admin.site.urls),
]
