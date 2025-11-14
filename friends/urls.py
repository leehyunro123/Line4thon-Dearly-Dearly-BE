from django.urls import path
from . import views

urlpatterns = [
    # 친구 요청
    path("requests", views.send_friend_request),                        # 친구 요청 보내기
    path("requests/received", views.received_friend_requests),          # 받은 요청 목록 조회
    path("requests/<int:pk>/accept", views.accept_friend_request),      # 친구 요청 수락
    path("requests/<int:pk>/reject", views.reject_friend_request),      # 친구 요청 거절

    # 친구 목록
    path("", views.friend_list),                                        # 친구 목록 조회
    path("<int:friend_id>/favorite", views.set_favorite_friend),        # 즐겨찾기 설정/해제
    path("<int:friend_id>", views.delete_friend),                       # 친구 삭제
    path("search", views.search_users),                                 # 아이디/닉네임으로 유저 검색
    path("<int:friend_id>/profile", views.friend_profile),              # 친구 프로필 요약 조회
]