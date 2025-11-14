from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from users.models import UserProfile


# ============================================================
# 공통 Serializers (카카오 + 자체 로그인 공용)
# ============================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 정보"""
    class Meta:
        model = UserProfile
        fields = ['real_name', 'nickname', 'profile_image', 'created_letterroom_count', 
                  'sent_letter_count', 'received_letter_count']
        read_only_fields = ['created_letterroom_count', 'sent_letter_count', 'received_letter_count']


class UserSerializer(serializers.ModelSerializer):
    """사용자 기본 정보 + 프로필"""
    user_id = serializers.CharField(source='username', read_only=True)
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'user_id', 'email', 'profile']
        read_only_fields = ['id', 'user_id', 'email']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """프로필 수정용 Serializer"""
    class Meta:
        model = UserProfile
        fields = ['real_name', 'nickname', 'profile_image']
    
    def validate_real_name(self, value):
        """실명 검증"""
        if value and len(value.strip()) == 0:
            raise serializers.ValidationError("실명은 공백만 입력할 수 없습니다.")
        return value.strip() if value else value


# ============================================================
# 자체 로그인 Serializers
# ============================================================

class RegisterSerializer(serializers.ModelSerializer):
    """회원가입용 Serializer"""
    user_id = serializers.CharField(
        source='username',  # DB에는 username으로 저장
        required=True,
        help_text="로그인 아이디 (영문/숫자)",
        label="아이디"
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'},
        label="비밀번호"
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        label="비밀번호 확인"
    )
    
    class Meta:
        model = User
        fields = ['user_id', 'password', 'password_confirm']
    
    def validate_user_id(self, value):
        """아이디 중복 검사"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 사용 중인 아이디입니다.")
        return value
    
    def validate(self, attrs):
        """비밀번호 확인"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "비밀번호가 일치하지 않습니다."
            })
        return attrs
    
    def create(self, validated_data):
        """사용자 생성"""
        # password_confirm 제거
        validated_data.pop('password_confirm')
        
        # User 생성 (비밀번호 해싱, 이메일 없이)
        user = User.objects.create_user(
            username=validated_data['username'],  # source로 자동 매핑됨
            password=validated_data['password']
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    """로그인용 Serializer"""
    user_id = serializers.CharField(
        required=True,
        help_text="로그인 아이디",
        label="아이디"
    )
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'},
        label="비밀번호"
    )
    
    def validate(self, attrs):
        """사용자 인증"""
        from django.contrib.auth import authenticate
        
        user_id = attrs.get('user_id')
        password = attrs.get('password')
        
        if user_id and password:
            # Django authenticate는 username 파라미터 사용
            user = authenticate(username=user_id, password=password)
            
            if not user:
                raise serializers.ValidationError(
                    "아이디 또는 비밀번호가 올바르지 않습니다."
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "비활성화된 계정입니다."
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                "아이디와 비밀번호를 모두 입력해주세요."
            )


class PasswordChangeSerializer(serializers.Serializer):
    """비밀번호 변경용 Serializer"""
    old_password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """현재 비밀번호 확인"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 일치하지 않습니다.")
        return value
    
    def validate(self, attrs):
        """새 비밀번호 확인"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "새 비밀번호가 일치하지 않습니다."
            })
        return attrs
    
    def save(self, **kwargs):
        """비밀번호 변경"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

