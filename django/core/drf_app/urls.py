from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SimpleItemViewSet

router = DefaultRouter()
router.register(r'items', SimpleItemViewSet)



urlpatterns = [
    path('', include(router.urls)),

]