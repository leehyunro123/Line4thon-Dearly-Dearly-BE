from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone
from letterrooms.models import LetterRoom
from letters.models import DirectLetter
from .models import Notification
from .serializers import NotificationSerializer

def _ensure_open_notifications(user):
    now = timezone.now()

    # 편지방: 이제 열렸는데 아직 알림 안 보낸 것
    rooms = LetterRoom.objects.filter(
        owner=user,
        open_at__lte=now,
        opened_noti_sent=False,
    )
    for room in rooms:
        Notification.objects.create(
            user=user,
            type=Notification.Type.ROOM_OPENED,
            title="편지방이 열렸어요",
            message=f"[{room.title}] 편지방을 열어볼 수 있어요.",
            letterroom=room,
        )
        room.opened_noti_sent = True
        room.save(update_fields=["opened_noti_sent"])

    # 1:1 편지: 이제 열 수 있게 된 것 (receiver 기준)
    letters = DirectLetter.objects.filter(
        receiver=user,
        open_at__lte=now,
        opened_noti_sent=False,
    )
    for dl in letters:
        Notification.objects.create(
            user=user,
            type=Notification.Type.DIRECT_OPENED,
            title="편지를 읽을 수 있어요",
            message="도착해 있던 편지를 열람할 수 있게 되었어요.",
            direct_letter=dl,
        )
        dl.opened_noti_sent = True
        dl.save(update_fields=["opened_noti_sent"])

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_list(request): # 접속할 때마다 D-day 체크
    _ensure_open_notifications(request.user) 
    #내 알림 목록 
    qs = Notification.objects.filter(user=request.user)
    if request.query_params.get("unread_only") == "true":
        qs = qs.filter(is_read=False)

    serializer = NotificationSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notification_read(request, pk):
    #알림 하나 읽음 처리
    try:
        noti = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response({"detail": "알림이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    noti.is_read = True
    noti.save(update_fields=["is_read"])
    return Response({"detail": "ok"}, status=status.HTTP_200_OK)
