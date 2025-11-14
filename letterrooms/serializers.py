from rest_framework import serializers
from django.urls import reverse
from .models import LetterRoom, RoomLetter


class LetterRoomSerializer(serializers.ModelSerializer):
    # 편지 센터 (편지방 메인 사진 안)에 "편지 N개" 표시용
    letters_count = serializers.IntegerField(source="letters.count", read_only=True)
    share_link = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LetterRoom
        fields = "__all__" 
    
    def get_share_link(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        
        path = reverse("letterroom_public", args=[obj.share_code])
        return request.build_absolute_uri(path)


class RoomLetterSerializer(serializers.ModelSerializer):
    # 방 공개일은 편지와 동일 -> 읽기 전용으로 같이 내려줌
    open_at = serializers.DateTimeField(source="letterroom.open_at", read_only=True)

    class Meta:
        model = RoomLetter
        fields = "__all__" 