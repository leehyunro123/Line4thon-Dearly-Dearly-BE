from django.db import models
from django.contrib.auth import get_user_model
from letterrooms.models import LetterRoom, RoomLetter
from letters.models import DirectLetter

User = get_user_model()

class Notification(models.Model):
    class Type(models.TextChoices):
        FRIEND_REQUEST = "FRIEND_REQUEST", "친구 요청"
        ROOM_NEW_LETTER = "ROOM_NEW_LETTER", "편지방 새 편지"
        DIRECT_LETTER = "DIRECT_LETTER", "1:1 편지 도착"
        ROOM_OPENED = "ROOM_OPENED", "편지방 열림"
        DIRECT_OPENED = "DIRECT_OPENED", "1:1 편지 열람 가능"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",  # 알림 받는 사람
    )
    type = models.CharField(max_length=30, choices=Type.choices)

    title = models.CharField(max_length=100)
    message = models.TextField(blank=True)

    # 프론트에서 어디로 이동할지 결정할 때 
    friend = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="related_notifications"
    )
    letterroom = models.ForeignKey(
        LetterRoom, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    room_letter = models.ForeignKey(
        RoomLetter, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    direct_letter = models.ForeignKey(
        DirectLetter, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_type_display()}] to {self.user}"
