from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class DirectLetter(models.Model): #1:1편지/나에게 쓰는편지

    class FontStyle(models.TextChoices):
        BASIC = "BASIC", "기본체"
        ROUND = "ROUND", "둥근체"
        SOFT = "SOFT", "부드러운체"
        ELEGANT = "ELEGANT", "우아한체"
        MODERN = "MODERN", "모던체"
        WARM = "WARM", "따뜻한체"

    class PaperTheme(models.TextChoices):
        WHITE = "WHITE", "흰색"
        PURPLE = "PURPLE", "보라색"
        PINK_HEART = "PINK_HEART", "핑크 하트"
        BLUE_SKY = "BLUE_SKY", "파란 하늘"
        GREEN_CLOVER = "GREEN_CLOVER", "초록 클로버"
        PEACH_BLOSSOM = "PEACH_BLOSSOM", "복숭아 꽃"

    # 발신자 / 수신자
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_direct_letters",
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_direct_letters",
    )

    # 폰트 / 편지지 / 내용
    font_style = models.CharField(
        max_length=20,
        choices=FontStyle.choices,
        default=FontStyle.BASIC,
    )
    paper_theme = models.CharField(
        max_length=20,
        choices=PaperTheme.choices,
        default=PaperTheme.WHITE,
    )
    content = models.TextField()

    #공개 날짜 
    open_at = models.DateTimeField()

    opened_noti_sent = models.BooleanField(default=False)


    #이미지 최대 3장/첫번쨰가 썸네일
    image1 = models.ImageField(upload_to="direct_letters/", blank=True, null=True)
    image2 = models.ImageField(upload_to="direct_letters/", blank=True, null=True)
    image3 = models.ImageField(upload_to="direct_letters/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property 
    def is_open(self):
        return timezone.now()>=self.open_at #현재열람가능?
    
    @property
    def is_self_letter(self):
        return self.sender_id == self.receiver_id
    
    class Meta:
        ordering = ['-created_at']