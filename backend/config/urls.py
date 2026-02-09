from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include


def health(_request):
    return HttpResponse("OK")


urlpatterns = [
    path("", health),
    path("admin/", admin.site.urls),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/transactions/", include("apps.transactions.urls")),
    path("api/v1/fraud/", include("apps.fraud.urls")),
    path("api/v1/realtime/", include("apps.realtime.urls")),
]
