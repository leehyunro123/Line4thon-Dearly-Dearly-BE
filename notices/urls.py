from django.urls import path
from . import views

urlpatterns = [
    path("notices/", views.notice_list),          # GET 목록 / POST 생성
    path("notices/<int:notice_id>/", views.notice_detail),
    path("notices/has-new/", views.has_new_notice),  # 새 공지 여부 확인
]
