from django.urls import path, include
from . import views

urlpatterns = [
    # ============================================================
    # 공통 인증 API (카카오 + 자체 로그인 공용)
    # ============================================================
    # 프로필 업데이트
    path('auth/profile/', views.update_profile, name='update-profile'),
    
    # 현재 사용자 정보 조회
    path('auth/user/', views.current_user, name='current-user'),
    
    # 로그아웃
    path('auth/logout/', views.logout, name='logout'),
    
    # ============================================================
    # 카카오 로그인 API
    # ============================================================
    # 카카오 로그인 완료 후 JWT 토큰 발급 (allauth 로그인 처리 후 호출됨)
    path('auth/kakao/done/', views.kakao_login_done, name='kakao-done'),
    
    # 카카오 로그인 (django-allauth 직접 사용)
    # GET /accounts/kakao/login/ - 카카오 로그인 시작
    # GET /accounts/kakao/login/callback/ - 카카오 콜백 (자동으로 로그인 처리)
    path('accounts/', include('allauth.urls')),
    
    # ============================================================
    # 자체 로그인 API
    # ============================================================
    # 아이디 중복 확인
    path('auth/check-user-id/', views.check_user_id, name='check-user-id'),
    
    # 회원가입
    path('auth/register/', views.register, name='register'),
    
    # 로그인
    path('auth/login/', views.login, name='login'),
    
    # 토큰 재발급
    path('auth/refresh/', views.token_refresh, name='token-refresh'),
    
    # 비밀번호 변경
    path('auth/password/change/', views.change_password, name='password-change'),
]

