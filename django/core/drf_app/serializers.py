from rest_framework import serializers

from .models import SimpleItem

class SimpleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimpleItem
        fields = "__all__"