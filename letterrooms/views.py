from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.urls import reverse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from notifications.models import Notification
from .models import LetterRoom, RoomLetter
from .serializers import LetterRoomSerializer, RoomLetterSerializer


# 내 편지방 목록 조회 (+ 정렬)
@api_view(["GET"])
def my_letterrooms(request):
    owner = request.GET.get("owner")
    sort = (request.GET.get("sort") or "recent").lower()

    qs = LetterRoom.objects.filter(owner=owner)
    if sort == "dday_asc":
        qs = qs.order_by("open_at")
    else:
        qs = qs.order_by("-created_at")

    serializer = LetterRoomSerializer(qs, many=True, context={"request": request})
    return Response(serializer.data)


# 편지방 생성
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def create_letterroom(request):
    in_ser = LetterRoomSerializer(data=request.data)
    if in_ser.is_valid():
        room = in_ser.save()
        out_ser = LetterRoomSerializer(room, context={"request": request}) 
        return Response(out_ser.data, status=status.HTTP_201_CREATED)
    return Response(in_ser.errors, status=status.HTTP_400_BAD_REQUEST)



# 편지방 삭제
@api_view(["DELETE"])
def delete_letterroom(request, id):
    room = get_object_or_404(LetterRoom, id=id)
    room.delete()
    return Response({"message": "deleted"}, status=status.HTTP_204_NO_CONTENT)


# 편지방 공유 링크 조회
@api_view(["GET"])
def get_share_link(request, id):
    room = get_object_or_404(LetterRoom, id=id)
    # /letterrooms/public/<code> 경로를 이름으로 역참조
    path = reverse("letterroom_public", args=[room.share_code])
    # 절대 URL로 변환 (ex: http://127.0.0.1:8000/letterrooms/public/abcd1234)
    absolute_url = request.build_absolute_uri(path)
    return Response({"share_link": absolute_url})


# 공유 링크로 편지방 조회 (로그인 / 비로그인 공통)
@api_view(["GET"])
def get_letterroom_by_sharecode(request, share_code):
    room = get_object_or_404(LetterRoom, share_code=share_code)
    serializer = LetterRoomSerializer(room, context={"request": request})
    return Response(serializer.data)


# 편지방 내 편지 목록 조회 / 편지 작성
@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser])
def letters_collection(request, id):
    room = get_object_or_404(LetterRoom, id=id)

    # --------------------- GET: 편지 목록 ---------------------
    if request.method == "GET":
        letters = RoomLetter.objects.filter(letterroom=room).order_by("-created_at")
        serializer = RoomLetterSerializer(letters, many=True)
        return Response(serializer.data)

    # --------------------- POST: 편지 작성 ---------------------
    data = request.data.copy()
    data["letterroom"] = room.id

    # 익명 허용 로직
    if not room.allow_anonymous:
        data["is_anonymous"] = False
    else:
        if "is_anonymous" in data:
            val = str(data["is_anonymous"]).lower()
            data["is_anonymous"] = val in ("1", "true", "t", "yes", "y")

    serializer = RoomLetterSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        letter = serializer.save()

        # 방 주인에게만 알림 (자기 방에 자기가 쓴 건 알림 X)
        if room.owner != request.user:
            Notification.objects.create(
                user=room.owner,
                type=Notification.Type.ROOM_NEW_LETTER,
                title="새 편지가 도착했어요",
                message=f"{request.user.username} 님이 [{room.title}]에 편지를 남겼어요.",
                letterroom=room,
                room_letter=letter,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 편지방 내 단일 편지 상세 조회
@api_view(["GET"])
def letter_detail(request, id, letter_id):
    letter = get_object_or_404(RoomLetter, id=letter_id, letterroom_id=id)
    serializer = RoomLetterSerializer(letter)
    return Response(serializer.data)