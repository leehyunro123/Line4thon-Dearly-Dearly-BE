from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FriendRequest, FriendShip
from letterrooms.models import LetterRoom, RoomLetter

User = get_user_model()


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user_username = serializers.CharField(source='from_user.username', read_only=True)
    to_user_username = serializers.CharField(source='to_user.username', read_only=True)

    class Meta:
        model = FriendRequest
        fields = [
            'id',
            'from_user',
            'from_user_username',
            'to_user',
            'to_user_username',
            'status',
            'created_at',
            'responded_at',
        ]
        read_only_fields = ['from_user', 'status', 'created_at', 'responded_at']


class SendFriendRequestSerializer(serializers.Serializer):
    to_user_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context['request']
        from_user = request.user
        to_user_id = attrs['to_user_id']

        if from_user.id == to_user_id:
            raise serializers.ValidationError("자기 자신에게 친구 요청을 보낼 수 없습니다.")

        # 대상 유저 존재 여부 확인
        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("해당 유저를 찾을 수 없습니다.")

        # 이미 대기중인 요청 있는지 확인
        if FriendRequest.objects.filter(
            from_user=from_user,
            to_user=to_user,
            status=FriendRequest.Status.PENDING
        ).exists():
            raise serializers.ValidationError("이미 친구 요청을 보냈습니다.")

        attrs['to_user'] = to_user
        return attrs

    def create(self, validated_data):
        from_user = self.context['request'].user
        to_user = validated_data['to_user']
        return FriendRequest.objects.create(
            from_user=from_user,
            to_user=to_user,
        )


# 친구 목록/프로필에서 보여줄 최소 유저 정보
# 닉네임 & 아이디
class SimpleUserSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField() # 프로필 닉네임 (없으면 username 사용)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname']

    def get_nickname(self, obj):
        # 1) User 인스턴스인 경우 (정상 케이스)
        if isinstance(obj, User):
            profile = getattr(obj, 'profile', None)
            if profile and getattr(profile, 'nickname', None):
                return profile.nickname
            return obj.username

        # 2) 이미 직렬화된 dict/ReturnDict로 들어온 경우 방어
        if isinstance(obj, dict):
            # nickname 있으면 사용, 없으면 username 사용
            return obj.get('nickname') or obj.get('username')

        return None


# 친구 목록용: 상대 유저 정보 & 즐겨찾기 여부
class FriendShipSerializer(serializers.ModelSerializer):
    friend = SimpleUserSerializer(read_only=True)

    class Meta:
        model = FriendShip
        fields = ['id', 'friend', 'is_favorite', 'created_at']


# 유저 검색 결과: 친구 여부 & 요청 상태
class UserSearchResultSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    is_friend = serializers.SerializerMethodField()
    has_sent_request = serializers.SerializerMethodField()
    has_received_request = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username', # ex) 아이디 (@eunji)
            'nickname', # ex) 닉네임 (은지)
            'is_friend',
            'has_sent_request',
            'has_received_request',
        ]

    def get_nickname(self, obj):
        profile = getattr(obj, 'profile', None)
        if profile and profile.nickname:
            return profile.nickname
        return obj.username

    def get_is_friend(self, obj):
        request = self.context['request']
        return FriendShip.objects.filter(user=request.user, friend=obj).exists()

    def get_has_sent_request(self, obj):
        request = self.context['request']
        return FriendRequest.objects.filter(
            from_user=request.user,
            to_user=obj,
            status=FriendRequest.Status.PENDING,
        ).exists()

    def get_has_received_request(self, obj):
        request = self.context['request']
        return FriendRequest.objects.filter(
            from_user=obj,
            to_user=request.user,
            status=FriendRequest.Status.PENDING,
        ).exists()


# ---친구 프로필용 서브 시리얼라이저 (친구 프로필 화면을 한 번에 구성하기 위함)---

# 친구 프로필 화면에서 보이는 편지방 목록
class LetterRoomSummarySerializer(serializers.ModelSerializer):
    letters_count = serializers.SerializerMethodField()  # 몇 명이 썼는지
    is_open = serializers.SerializerMethodField()        # 오픈 여부
    owner = SimpleUserSerializer(read_only=True)  # 편지방 주인 이름

    class Meta:
        model = LetterRoom
        fields = [
            'id',
            'title',
            'visibility',
            'is_open',
            'letters_count',
            'owner',
            'share_code',
        ]

    def get_letters_count(self, obj):
        return obj.letters.count()

    def get_is_open(self, obj):
        return obj.is_open


# 친구 프로필 화면에서 받은 편지와 보낸 편지 목록 요약
class RoomLetterSummarySerializer(serializers.ModelSerializer):
    letterroom_id = serializers.IntegerField(source='letterroom.id', read_only=True)

    class Meta:
        model = RoomLetter
        fields = ['id', 'letterroom_id', 'content', 'created_at']


# 개인 프로필 눌렀을 때 화면
class FriendProfileSerializer(serializers.Serializer):
    friend = SimpleUserSerializer()
    is_favorite = serializers.BooleanField()
    letterrooms_count = serializers.IntegerField()
    letterrooms = LetterRoomSummarySerializer(many=True)
    letters_sent_count = serializers.IntegerField()
    letters_sent = RoomLetterSummarySerializer(many=True)
    letters_received_count = serializers.IntegerField()
    letters_received = RoomLetterSummarySerializer(many=True)