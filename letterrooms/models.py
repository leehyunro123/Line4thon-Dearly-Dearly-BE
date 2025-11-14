import uuid # 편지방 공유 코드 자동으로 랜덤 생성
from django.db import models
from django.utils import timezone
from django.conf import settings

# 편지방 모델
class LetterRoom(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC_ALL = "PUBLIC_ALL", "전체 공개"
        PUBLIC_FRIENDS = "PUBLIC_FRIENDS", "친구만"

    class WritePermission(models.TextChoices):
        WRITE_ALL = "WRITE_ALL", "누구나 작성 가능"
        WRITE_FRIENDS = "WRITE_FRIENDS", "친구만"
        WRITE_INVITED = "WRITE_INVITED", "초대 링크만"

    # 로그인 후 연동 확인 필요 (owner)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="letterrooms")
    title = models.CharField(max_length=100) # 편지방 제목
    cover_image = models.ImageField(upload_to="letterrooms/covers/", blank=True, null=True) # 커버 이미지(사용자 업로드)
    open_at = models.DateTimeField() # 디데이 공개 날짜
    opened_noti_sent = models.BooleanField(default=False)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC_ALL) # 공개 범위 
    write_permission = models.CharField(max_length=20, choices=WritePermission.choices, default=WritePermission.WRITE_ALL) # 편지방 작성 권한
    allow_anonymous = models.BooleanField(default=True) # 익명 허용 여부
    share_code = models.CharField(max_length=12, unique=True, editable=False) # 공유 링크용 랜덤 코드
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.share_code:
            self.share_code = uuid.uuid4().hex[:8]
        super().save(*args, **kwargs)

    @property
    def is_open(self): 
        return timezone.now() >= self.open_at

    class Meta: ordering = ["-created_at"]


# 편지방 속의 편지 전용 모델
class RoomLetter(models.Model):
    class FontStyle(models.TextChoices): # 폰트 6종 중 택 1
        BASIC = "BASIC", "기본체"
        ROUND = "ROUND", "둥근체"
        SOFT = "SOFT", "부드러운체"
        ELEGANT = "ELEGANT", "우아한체"
        MODERN = "MODERN", "모던체"
        WARM = "WARM", "따뜻한체"

    class PaperTheme(models.TextChoices): # 편지지 6종 중 택 1
        WHITE = "WHITE", "흰색"
        PURPLE = "PURPLE", "보라색"
        PINK_HEART = "PINK_HEART", "핑크 하트"
        BLUE_SKY = "BLUE_SKY", "파란 하늘"
        GREEN_CLOVER = "GREEN_CLOVER", "초록 클로버"
        PEACH_BLOSSOM = "PEACH_BLOSSOM", "복숭아 꽃"

    letterroom = models.ForeignKey(LetterRoom, on_delete=models.CASCADE, related_name="letters")

    # 로그인 후 연동 확인 필요 (author)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="room_letters") # 익명 허용 위해 null/blank 허용
    is_anonymous = models.BooleanField(default=False) # 디폴트는 닉네임 공개
    font_style = models.CharField(max_length=20, choices=FontStyle.choices, default=FontStyle.BASIC)
    paper_theme = models.CharField(max_length=20, choices=PaperTheme.choices, default=PaperTheme.WHITE)
    content = models.TextField()
    image = models.ImageField(upload_to="letters/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]