from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('drf-api/', include('drf_app.urls')),
    path('', include('api.urls')),
]
