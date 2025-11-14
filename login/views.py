from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    LoginSerializer, 
    PasswordChangeSerializer,
    ProfileUpdateSerializer
)


def get_tokens_for_user(user):
    """사용자에 대한 JWT 토큰 생성"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@extend_schema(
    summary="현재 로그인한 사용자 정보 조회",
    description="JWT 토큰을 사용하여 현재 로그인한 사용자의 정보를 조회합니다.",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="인증 실패 (토큰 없음 또는 만료)"),
    },
    tags=["인증"],
)
@extend_schema(
    summary="프로필 업데이트",
    description="""
    현재 로그인한 사용자의 프로필을 수정합니다.
    
    **수정 가능한 항목:**
    - `real_name`: 실명 (편지방 owner에 표시됨)
    - `nickname`: 닉네임
    - `profile_image`: 프로필 이미지
    
    **주의:**
    - 실명은 편지방 생성 시 owner 필드에 사용됩니다
    - 편지방 생성 전에 실명을 반드시 설정해야 합니다
    """,
    request=ProfileUpdateSerializer,
    responses={
        200: OpenApiResponse(
            description="프로필 업데이트 성공",
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        "message": "프로필이 업데이트되었습니다.",
                        "profile": {
                            "real_name": "홍길동",
                            "nickname": "길동이",
                            "profile_image": "/media/profiles/image.jpg"
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="잘못된 입력"),
        401: OpenApiResponse(description="인증 실패"),
    },
    tags=["인증"],
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    프로필 업데이트
    PATCH /auth/profile/
    """
    profile = request.user.profile
    serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "프로필이 업데이트되었습니다.",
            "profile": serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    현재 로그인한 사용자 정보 조회
    GET /auth/user/
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@extend_schema(
    summary="로그아웃",
    description="JWT Refresh 토큰을 블랙리스트에 추가하여 로그아웃합니다.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': 'JWT Refresh 토큰',
                }
            },
            'required': ['refresh'],
            'example': {
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description="로그아웃 성공",
            examples=[
                OpenApiExample(
                    'Success',
                    value={'message': '로그아웃 성공'}
                )
            ]
        ),
        400: OpenApiResponse(description="로그아웃 실패 (잘못된 토큰)"),
        401: OpenApiResponse(description="인증 실패"),
    },
    tags=["인증"],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    로그아웃 (JWT 토큰 블랙리스트 처리)
    POST /auth/logout/
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response(
            {"message": "로그아웃 성공"},
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {"error": "로그아웃 실패"},
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    summary="카카오 로그인 완료 - JWT 토큰 발급 및 프론트엔드 리다이렉트",
    description="""
    django-allauth가 카카오 로그인을 처리한 후 호출되는 엔드포인트입니다.
    
    **전체 플로우:**
    1. `/accounts/kakao/login/` - 카카오 로그인 시작
    2. 카카오 인증 완료
    3. `/accounts/kakao/login/callback/` - allauth가 자동으로 세션 로그인 처리
    4. **이 엔드포인트(`/auth/kakao/done/`)** - JWT 토큰 생성 후 프론트엔드로 리다이렉트
    5. 프론트엔드 `/auth/kakao/callback` - 토큰을 쿼리 파라미터로 수신
    
    **리다이렉트 URL:**
    - 성공: `{FRONTEND_URL}/auth/kakao/callback?access={access_token}&refresh={refresh_token}&user_id={user_id}`
    - 실패: `{FRONTEND_URL}/auth/kakao/callback?error=login_failed`
    
    **주의:** 
    - 이 API는 Swagger에서 직접 테스트할 수 없습니다.
    - 반드시 카카오 로그인 플로우를 통해서만 호출됩니다.
    - 이 시점에서 `request.user`는 이미 로그인된 상태입니다.
    """,
    responses={
        302: OpenApiResponse(description="프론트엔드로 리다이렉트"),
    },
    tags=["카카오 로그인"],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def kakao_login_done(request):
    """
    카카오 로그인 완료 후 JWT 토큰 발급 및 프론트엔드 리다이렉트
    GET /auth/kakao/done/
    
    이 view는 django-allauth가 로그인 처리를 완료한 후 호출됩니다.
    따라서 request.user는 이미 인증된 상태입니다.
    """
    from django.conf import settings
    
    if request.user.is_authenticated:
        tokens = get_tokens_for_user(request.user)
        access = tokens["access"]
        refresh = tokens["refresh"]
        user_id = request.user.username
        
        frontend = settings.FRONTEND_URL
        return redirect(
            f"{frontend}/auth/kakao/callback?access={access}&refresh={refresh}&user_id={user_id}"
        )
    
    # 로그인 실패 시 (정상적인 경우 여기로 오면 안됨)
    return redirect(f"{settings.FRONTEND_URL}/auth/kakao/callback?error=login_failed")


# ============================================================
# 자체 로그인 Views
# ============================================================

@extend_schema(
    summary="아이디 중복 확인",
    description="""
    회원가입 전 아이디 중복을 확인합니다.
    
    **사용 시점:**
    - 회원가입 폼에서 아이디 입력 후
    - "중복 확인" 버튼 클릭 시
    - 아이디 입력란 포커스 아웃 시 (실시간 검증)
    
    **응답:**
    - `available: true` - 사용 가능한 아이디
    - `available: false` - 이미 사용 중인 아이디
    """,
    parameters=[
        OpenApiParameter(
            name='user_id',
            type=str,
            location=OpenApiParameter.QUERY,
            description='확인할 아이디',
            required=True,
            examples=[
                OpenApiExample(
                    'Example',
                    value='testuser'
                )
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            description="중복 확인 완료",
            examples=[
                OpenApiExample(
                    'Available',
                    value={
                        "available": True,
                        "message": "사용 가능한 아이디입니다."
                    }
                ),
                OpenApiExample(
                    'Not Available',
                    value={
                        "available": False,
                        "message": "이미 사용 중인 아이디입니다."
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="잘못된 요청",
            examples=[
                OpenApiExample(
                    'Missing Parameter',
                    value={"error": "user_id 파라미터가 필요합니다."}
                )
            ]
        ),
    },
    tags=["자체 로그인"],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def check_user_id(request):
    """
    아이디 중복 확인
    GET /auth/check-user-id/?user_id=testuser
    """
    from django.contrib.auth.models import User
    
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return Response(
            {"error": "user_id 파라미터가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 아이디 중복 검사
    is_taken = User.objects.filter(username=user_id).exists()
    
    if is_taken:
        return Response({
            "available": False,
            "message": "이미 사용 중인 아이디입니다."
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "available": True,
            "message": "사용 가능한 아이디입니다."
        }, status=status.HTTP_200_OK)


@extend_schema(
    summary="회원가입",
    description="""
    자체 로그인을 위한 회원가입 API입니다.
    
    **필수 입력:**
    - `user_id`: 로그인 아이디 (영문/숫자 조합, 중복 불가)
    - `password`: 비밀번호 (최소 8자 이상)
    - `password_confirm`: 비밀번호 확인
    
    **비밀번호 규칙:**
    - 최소 8자 이상
    - 숫자, 문자 조합 권장
    - 너무 흔한 비밀번호는 사용 불가
    
    **참고:**
    - 회원가입 시 UserProfile이 자동으로 생성됩니다
    """,
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="회원가입 성공",
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        "message": "회원가입 성공",
                        "user": {
                            "id": 1,
                            "user_id": "testuser",
                            "email": ""
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="입력 데이터 오류",
            examples=[
                OpenApiExample(
                    'User ID Exists',
                    value={"user_id": ["이미 사용 중인 아이디입니다."]}
                ),
                OpenApiExample(
                    'Password Mismatch',
                    value={"password_confirm": ["비밀번호가 일치하지 않습니다."]}
                ),
            ]
        ),
    },
    tags=["자체 로그인"],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    회원가입
    POST /auth/register/
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        user_data = UserSerializer(user).data
        
        return Response({
            "message": "회원가입 성공",
            "user": user_data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="로그인",
    description="""
    아이디와 비밀번호로 로그인하여 JWT 토큰을 발급받습니다.
    
    **필수 입력:**
    - `user_id`: 로그인 아이디 (회원가입 시 등록한 아이디)
    - `password`: 비밀번호
    
    **응답:**
    - `access`: API 요청에 사용하는 액세스 토큰 (유효기간: 60분)
    - `refresh`: 액세스 토큰 재발급용 리프레시 토큰 (유효기간: 14일)
    - `user`: 사용자 정보 (id는 숫자 PK, user_id는 로그인 아이디)
    
    **사용 방법:**
    1. 로그인으로 토큰 발급
    2. API 요청 시 Header에 `Authorization: Bearer {access_token}` 추가
    3. 액세스 토큰 만료 시 `/auth/refresh/`로 재발급
    """,
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="로그인 성공",
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        "message": "로그인 성공",
                        "tokens": {
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        },
                        "user": {
                            "id": 1,
                            "user_id": "testuser",
                            "email": ""
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="로그인 실패",
            examples=[
                OpenApiExample(
                    'Invalid Credentials',
                    value={"non_field_errors": ["아이디 또는 비밀번호가 올바르지 않습니다."]}
                ),
                OpenApiExample(
                    'Inactive Account',
                    value={"non_field_errors": ["비활성화된 계정입니다."]}
                ),
            ]
        ),
    },
    tags=["자체 로그인"],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    로그인 (JWT 토큰 발급)
    POST /auth/login/
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        user_data = UserSerializer(user).data
        
        return Response({
            "message": "로그인 성공",
            "tokens": tokens,
            "user": user_data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="토큰 재발급",
    description="""
    Refresh 토큰을 사용하여 새로운 Access 토큰을 발급받습니다.
    
    **사용 시점:**
    - Access 토큰이 만료되었을 때 (401 Unauthorized)
    - Refresh 토큰은 아직 유효할 때
    
    **주의:**
    - Refresh 토큰도 만료된 경우 다시 로그인해야 합니다.
    - 새 토큰 발급 시 이전 Refresh 토큰은 무효화됩니다.
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': 'Refresh 토큰',
                }
            },
            'required': ['refresh'],
            'example': {
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            }
        }
    },
    responses={
        200: OpenApiResponse(
            description="토큰 재발급 성공",
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="잘못된 토큰"),
        401: OpenApiResponse(description="만료된 토큰"),
    },
    tags=["자체 로그인"],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh(request):
    """
    Access 토큰 재발급
    POST /auth/refresh/
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {"error": "refresh 토큰이 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        
        # 새로운 액세스 토큰 발급
        access_token = str(refresh.access_token)
        
        # Refresh 토큰 회전 (새 refresh 토큰 발급)
        refresh.set_jti()
        refresh.set_exp()
        new_refresh_token = str(refresh)
        
        return Response({
            "access": access_token,
            "refresh": new_refresh_token
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": "유효하지 않거나 만료된 토큰입니다."},
            status=status.HTTP_401_UNAUTHORIZED
        )


@extend_schema(
    summary="비밀번호 변경",
    description="""
    현재 로그인한 사용자의 비밀번호를 변경합니다.
    
    **요구사항:**
    - JWT 인증 필요 (Authorization Header)
    - 현재 비밀번호 확인 필수
    - 새 비밀번호는 Django 비밀번호 검증 규칙 준수
    
    **주의:**
    - 비밀번호 변경 후 기존 토큰은 유효합니다.
    - 보안을 위해 변경 후 재로그인을 권장합니다.
    """,
    request=PasswordChangeSerializer,
    responses={
        200: OpenApiResponse(
            description="비밀번호 변경 성공",
            examples=[
                OpenApiExample(
                    'Success',
                    value={"message": "비밀번호가 성공적으로 변경되었습니다."}
                )
            ]
        ),
        400: OpenApiResponse(
            description="입력 데이터 오류",
            examples=[
                OpenApiExample(
                    'Wrong Current Password',
                    value={"old_password": ["현재 비밀번호가 일치하지 않습니다."]}
                ),
                OpenApiExample(
                    'Password Mismatch',
                    value={"new_password_confirm": ["새 비밀번호가 일치하지 않습니다."]}
                ),
            ]
        ),
        401: OpenApiResponse(description="인증 실패 (로그인 필요)"),
    },
    tags=["자체 로그인"],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    비밀번호 변경
    POST /auth/password/change/
    """
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "비밀번호가 성공적으로 변경되었습니다."},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
