from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.signals import pre_social_login
from allauth.account.signals import user_signed_up


# 소셜 로그인 시 자동으로 UserProfile 생성
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """User 생성 시 자동으로 UserProfile 생성"""
    if created:
        from users.models import UserProfile
        UserProfile.objects.get_or_create(user=instance)


@receiver(user_signed_up)
def populate_profile_on_social_login(request, user, sociallogin=None, **kwargs):
    """
    소셜 로그인 시 카카오에서 받은 정보로 UserProfile 자동 채우기
    """
    if sociallogin:
        # 카카오 로그인인 경우
        if sociallogin.account.provider == 'kakao':
            extra_data = sociallogin.account.extra_data
            
            # UserProfile 가져오기 또는 생성
            from users.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # 카카오에서 제공하는 정보 저장
            if 'kakao_account' in extra_data:
                kakao_account = extra_data['kakao_account']
                
                # 닉네임 설정 (properties에서 nickname 가져오기)
                if 'profile' in kakao_account:
                    nickname = kakao_account['profile'].get('nickname', '')
                    if nickname and not profile.nickname:
                        profile.nickname = nickname
                
                # 프로필 이미지 URL (저장은 하지 않고 참고용)
                # 실제 이미지 다운로드 후 저장하려면 추가 로직 필요
                if 'profile' in kakao_account:
                    profile_image_url = kakao_account['profile'].get('profile_image_url', '')
                    # profile_image_url을 사용하여 이미지 다운로드 및 저장 가능
            
            profile.save()


# 카카오 로그인 시 기존 계정과 자동 연결 (이메일이 같을 경우)
@receiver(pre_social_login)
def link_to_local_user(sender, request, sociallogin, **kwargs):
    """
    소셜 로그인 시도 시 이미 같은 이메일로 가입된 계정이 있다면 연결
    """
    # 이메일이 없는 경우는 스킵
    email = sociallogin.account.extra_data.get('kakao_account', {}).get('email')
    if not email:
        return
    
    # 이미 연결된 계정이 있으면 스킵
    if sociallogin.is_existing:
        return
    
    # 같은 이메일의 User가 있는지 확인
    try:
        user = User.objects.get(email=email)
        # 소셜 계정을 기존 유저와 연결
        sociallogin.connect(request, user)
    except User.DoesNotExist:
        pass
