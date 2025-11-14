from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q, F               # 친구 목록
from django.db.models.signals import post_save  # 친구 목록
from django.dispatch import receiver            # 친구 목록

User = get_user_model()

# 친구 요청 관련
class FriendRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_friend_requests',
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_friend_requests',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(from_user=models.F('to_user')),
                name='friendrequest_no_self_request',
            ),
        ]

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"

    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.PENDING


# 친구 목록
class FriendShip(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friendships',      # 내가 친구로 추가한 사람들
    )
    friend = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friend_of',        # 나를 친구로 가진 사람들
    )
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'friend')
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=~Q(user=F('friend')),
                name='friendship_no_self',
            ),
        ]

    def __str__(self):
        return f"{self.user} -> {self.friend} ({'★' if self.is_favorite else ''})"


# FriendRequest 수락 시 자동으로 양방향 FriendShip 생성
@receiver(post_save, sender=FriendRequest)
def create_friendship_on_accept(sender, instance: FriendRequest, **kwargs):
    if instance.status == FriendRequest.Status.ACCEPTED:
        # from_user 입장
        FriendShip.objects.get_or_create(
            user=instance.from_user,
            friend=instance.to_user,
        )
        # to_user 입장
        FriendShip.objects.get_or_create(
            user=instance.to_user,
            friend=instance.from_user,
        )