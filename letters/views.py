from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.decorators import (api_view, permission_classes, parser_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from notifications.models import Notification
from users.models import UserProfile
from .serializers import DirectLetterSerializer
# Create your views here.

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_direct_letter(request):
    from .models import DirectLetter
    serializer = DirectLetterSerializer(
        data = request.data,
        context = {"request":request},
    )
    if serializer.is_valid():
        letter = serializer.save()

        # 나에게 쓰는 편지는 알림 X, 상대방에게만 알림
        if letter.sender != letter.receiver:
            Notification.objects.create(
                user=letter.receiver,
                type=Notification.Type.DIRECT_LETTER,
                title="새 1:1 편지가 도착했어요",
                message=f"{letter.sender.username} 님이 편지를 보냈어요.",
                direct_letter=letter,
            )

        #통계 카운트
        sender_profile,_ = UserProfile.objects.get_or_create(user=letter.sender)
        receiver_profile, _ = UserProfile.objects.get_or_create(user=letter.receiver)

        # 나에게 쓴 편지는 통계에서 제외
        if letter.sender != letter.receiver:
            sender_profile.sent_letter_count += 1
            sender_profile.save(update_fields=["sent_letter_count"])

            receiver_profile.received_letter_count += 1
            receiver_profile.save(update_fields=["received_letter_count"])
        # (sender == receiver일 땐 아무 통계도 증가시키지 않음)

        out_ser = DirectLetterSerializer(letter, context={"request": request})
        return Response(out_ser.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def direct_letter_inbox(request):
    from .models import DirectLetter

    user = request.user
    box = (request.GET.get("box") or "received").lower()
    partner_id = request.GET.get("partner_id")
    sort = (request.GET.get("sort") or "latest").lower()

    # 1) 기본: self 편지는 제외
    if box == "sent":
        qs = DirectLetter.objects.filter(sender=user).exclude(receiver=user)
    else:  # received
        qs = DirectLetter.objects.filter(receiver=user).exclude(sender=user)

    # 2) 특정 친구와의 편지만 보기
    if partner_id:
        try:
            partner_id = int(partner_id)
        except ValueError:
            return Response({"detail": "partner_id must be integer"}, status=400)

        # partner_id == 나 → 아래 /self/에서 처리
        if partner_id != user.id:
            if box == "sent":
                qs = qs.filter(receiver_id=partner_id)
            else:
                qs = qs.filter(sender_id=partner_id)

    # 3) 정렬
    if sort == "oldest":
        qs = qs.order_by("created_at")
    else:  # latest (default)
        qs = qs.order_by("-created_at")

    serializer = DirectLetterSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)

#나에게 쓴 편지 분리
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def self_letter_inbox(request):
    from .models import DirectLetter

    user = request.user
    sort = (request.GET.get("sort") or "latest").lower()

    # sender == receiver == 나
    qs = DirectLetter.objects.filter(sender=user, receiver=user)

    if sort == "oldest":
        qs = qs.order_by("created_at")
    else:
        qs = qs.order_by("-created_at")

    serializer = DirectLetterSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def direct_letter_detail(request, id):
    from .models import DirectLetter
    letter = get_object_or_404(DirectLetter, id=id)

    # 나와 무관한 편지 접근 차단
    if letter.sender != request.user and letter.receiver != request.user:
        return Response({"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

    serializer = DirectLetterSerializer(letter, context={"request": request})
    return Response(serializer.data, status=status.HTTP_200_OK)