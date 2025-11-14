from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q # 친구 목록
from django.contrib.auth import get_user_model # 친구 목록
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes # 두번째꺼는 친구 목록
from rest_framework.response import Response

from .models import FriendRequest, FriendShip
from notifications.models import Notification
from .serializers import FriendRequestSerializer, SendFriendRequestSerializer
from .serializers import ( # 친구 목록
    FriendShipSerializer,
    UserSearchResultSerializer,
    FriendProfileSerializer,
    SimpleUserSerializer, 
    LetterRoomSummarySerializer,
    RoomLetterSummarySerializer,
)
from letterrooms.models import LetterRoom, RoomLetter
from letters.models import DirectLetter 

User = get_user_model()


# ----- 친구 요청 -----

# 친구 요청 보내기  // body: { "to_user_id": <int> }
@api_view(['POST'])
def send_friend_request(request):
    serializer = SendFriendRequestSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        friend_request = serializer.save()

        #  알림 생성 (받는 사람: to_user)
        Notification.objects.create(
            user=friend_request.to_user,
            type=Notification.Type.FRIEND_REQUEST,
            title="새 친구 요청이 도착했어요",
            message=f"{request.user.username} 님이 친구를 신청했어요.",
            friend=request.user,
        )

        return Response(FriendRequestSerializer(friend_request).data,
                        status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 친구 요청 수락
@api_view(['POST'])
def accept_friend_request(request, pk):
    try:
        friend_request = FriendRequest.objects.get(
            pk=pk,
            to_user=request.user,
            status=FriendRequest.Status.PENDING
        )
    except FriendRequest.DoesNotExist:
        return Response({'error': '해당 요청이 없거나 이미 처리되었습니다.'},
                        status=status.HTTP_404_NOT_FOUND)

    friend_request.status = FriendRequest.Status.ACCEPTED
    friend_request.responded_at = timezone.now()
    friend_request.save()

    return Response(FriendRequestSerializer(friend_request).data,
                    status=status.HTTP_200_OK)


# 친구 요청 거절
@api_view(['POST'])
def reject_friend_request(request, pk):
    try:
        friend_request = FriendRequest.objects.get(
            pk=pk,
            to_user=request.user,
            status=FriendRequest.Status.PENDING
        )
    except FriendRequest.DoesNotExist:
        return Response({'error': '해당 요청이 없거나 이미 처리되었습니다.'},
                        status=status.HTTP_404_NOT_FOUND)

    friend_request.status = FriendRequest.Status.REJECTED
    friend_request.responded_at = timezone.now()
    friend_request.save()

    return Response(FriendRequestSerializer(friend_request).data,
                    status=status.HTTP_200_OK)


# 받은 친구 요청 목록 조회
@api_view(['GET'])
def received_friend_requests(request):
    qs = FriendRequest.objects.filter(
        to_user=request.user,
        status=FriendRequest.Status.PENDING
    )
    serializer = FriendRequestSerializer(qs, many=True)
    return Response(
        {
            'count': qs.count(),
            'results': serializer.data,
        },
        status=status.HTTP_200_OK
    )


# ----- 친구 목록 -----

# 친구 목록 조회
@api_view(['GET'])
def friend_list(request):
    qs = FriendShip.objects.filter(user=request.user).select_related('friend')
    serializer = FriendShipSerializer(qs, many=True)
    return Response(
        {
            'count': qs.count(),
            'results': serializer.data,
        },
        status=status.HTTP_200_OK,
    )


# 즐겨찾기 설정/해제 (최대 10명)
@api_view(['POST'])
def set_favorite_friend(request, friend_id):
    try:
        friendship = FriendShip.objects.get(user=request.user, friend_id=friend_id)
    except FriendShip.DoesNotExist:
        return Response({'detail': '친구 관계가 아닙니다.'}, status=status.HTTP_404_NOT_FOUND)

    raw = request.data.get('is_favorite')
    if raw in [True, 'true', 'True', '1', 1]:
        is_favorite = True
    elif raw in [False, 'false', 'False', '0', 0]:
        is_favorite = False
    else:
        return Response({'detail': 'is_favorite 값을 true/false 로 보내주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # 즐겨찾기 추가 시에만 카운트 체크
    if is_favorite and not friendship.is_favorite:
        current_count = FriendShip.objects.filter(
            user=request.user,
            is_favorite=True
        ).count()
        if current_count >= 10:
            return Response({'detail': '즐겨찾기는 최대 10명까지 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    friendship.is_favorite = is_favorite
    friendship.save()
    return Response(FriendShipSerializer(friendship).data, status=status.HTTP_200_OK)


# 친구 삭제
@api_view(['DELETE'])
def delete_friend(request, friend_id):
    # 양방향 모두 삭제
    deleted, _ = FriendShip.objects.filter(
        Q(user=request.user, friend_id=friend_id) |
        Q(user_id=friend_id, friend=request.user)
    ).delete()

    if deleted == 0:
        return Response({'detail': '친구 관계가 아닙니다.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_204_NO_CONTENT)


# 아이디/닉네임으로 유저 검색 (전체 유저 대상)
@api_view(['GET'])
def search_users(request):
    query = request.query_params.get('q', '').strip()
    if not query:
        return Response({'detail': '아이디나 닉네임으로 유저를 검색하세요.'}, status=status.HTTP_400_BAD_REQUEST)

    # 아이디(username) 또는 닉네임(UserProfile.nickname)으로 검색
    qs = User.objects.filter(
        Q(username__icontains=query) |          # 아이디 검색 (@뒤에 들어갈 값)
        Q(profile__nickname__icontains=query)   # 닉네임 검색 (OneToOne related_name='profile')
    ).exclude(id=request.user.id).select_related('profile')[:30]

    serializer = UserSearchResultSerializer(
        qs,
        many=True,
        context={'request': request},
    )

    # 이 응답의 id를 그대로 POST /friends/requests 의 to_user_id 로 사용하면 된당
    return Response(
        {
            'count': len(serializer.data),
            'results': serializer.data,
        },
        status=status.HTTP_200_OK,
    )


# 친구 프로필(요약 화면) 조회
@api_view(['GET'])
def friend_profile(request, friend_id):

    # 친구 유저 객체
    try:
        friend = User.objects.get(pk=friend_id)
    except User.DoesNotExist:
        return Response({'detail': '존재하지 않는 사용자입니다.'},
                        status=status.HTTP_404_NOT_FOUND)

    # 실제 친구인지 확인
    try:
        friendship = FriendShip.objects.get(user=request.user, friend=friend)
    except FriendShip.DoesNotExist:
        return Response({'detail': '친구가 아닌 사용자입니다.'},
                        status=status.HTTP_403_FORBIDDEN)

    # 공개된 편지방 목록 (PUBLIC_ALL + PUBLIC_FRIENDS)
    visible_rooms = LetterRoom.objects.filter(
        owner=friend,
        visibility__in=[
            LetterRoom.Visibility.PUBLIC_ALL,
            LetterRoom.Visibility.PUBLIC_FRIENDS,
        ],
    ).order_by('-created_at')

    # 내가 이 친구에게 보낸 1:1 편지들
    letters_sent = DirectLetter.objects.filter(
        sender=request.user,
        receiver=friend,
    ).order_by('-created_at')

    # 친구가 나에게 보낸 1:1 편지들
    letters_received = DirectLetter.objects.filter(
        sender=friend,
        receiver=request.user,
    ).order_by('-created_at')

    payload = {
        "friend": friend,
        "is_favorite": friendship.is_favorite,
        "letterrooms": visible_rooms,
        "letterrooms_count": visible_rooms.count(),
        "letters_sent": letters_sent,
        "letters_sent_count": letters_sent.count(),
        "letters_received": letters_received,
        "letters_received_count": letters_received.count(),
    }

    serializer = FriendProfileSerializer(payload)
    return Response(serializer.data, status=status.HTTP_200_OK)