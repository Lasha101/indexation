from rest_framework import viewsets
from .models import SimpleItem
from .serializers import SimpleItemSerializer

class SimpleItemViewSet(viewsets.ModelViewSet):
    queryset = SimpleItem.objects.all()
    serializer_class = SimpleItemSerializer
    