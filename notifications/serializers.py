from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "type", "title", "message",
            "friend", "letterroom", "room_letter", "direct_letter",
            "is_read", "created_at",
        ]
