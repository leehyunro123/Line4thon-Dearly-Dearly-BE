from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DirectLetter


class UserMinSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source="profile.nickname", read_only=True)
    profile_image = serializers.ImageField(source="profile.profile_image", read_only=True)

    class Meta:
        model = User
        fields = ["id", "nickname", "profile_image"]


class DirectLetterSerializer(serializers.ModelSerializer):
    sender = UserMinSerializer(read_only=True)
    receiver = UserMinSerializer(read_only=True)
    receiver_id = serializers.IntegerField(write_only=True)
    is_open = serializers.ReadOnlyField()
    is_self_letter = serializers.ReadOnlyField()

    class Meta:
        model = DirectLetter   
        fields = [
            "id", "sender", "receiver", "receiver_id",
            "font_style", "paper_theme", "content",
            "open_at", "image1", "image2", "image3",
            "is_open", "is_self_letter", "created_at",
        ]

    def create(self, validated_data):

        request = self.context["request"]
        sender = request.user
        receiver_id = validated_data.pop("receiver_id")
        receiver = User.objects.get(id=receiver_id)

        letter = DirectLetter.objects.create(
            sender=sender,
            receiver=receiver,
            **validated_data,
        )
        return letter
