from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)  # 아이디(@어쩌고)
    profile_image = serializers.ImageField(required=False)  
    nickname = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = [
            'username',
            'nickname',
            'profile_image',
            'created_letterroom_count',
            'sent_letter_count',
            'received_letter_count',
        ]
