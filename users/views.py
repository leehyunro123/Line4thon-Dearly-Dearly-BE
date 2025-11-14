# users/views.py
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import UserProfile
from .serializers import UserProfileSerializer


class UserProfileViewSet(mixins.RetrieveModelMixin,viewsets.GenericViewSet):
    
    #/api/users/<int:pk>/   -> 특정 유저 프로필 조회 (id 기반)
    #/api/users/me/         -> me : 현재 로그인한 유저 프로필 조회/수정
    
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        # pk는 user.id
        user_id = kwargs.get("pk")
        profile = get_object_or_404(UserProfile, user__id=user_id)
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        
        #GET  /api/users/me/   -> 내 프로필 조회
        #PATCH /api/users/me/  -> 내 프로필 부분 수정 (닉네임/이미지 등)
        
        # 현재 로그인한 유저의 프로필을 없으면 생성
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if request.method.lower() == "get":
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # 부분 수정
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
