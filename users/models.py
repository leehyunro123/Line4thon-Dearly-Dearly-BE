from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    real_name = models.CharField(max_length=20, blank=True, verbose_name="실명")  # 편지방 owner에 표시될 실명
    nickname = models.CharField(max_length=20, blank=True, verbose_name="닉네임")
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_letterroom_count = models.IntegerField(default=0)
    sent_letter_count = models.IntegerField(default=0)
    received_letter_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.real_name or '이름 미설정'}"

