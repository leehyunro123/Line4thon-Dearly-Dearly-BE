from django.urls import path
from . import views

urlpatterns = [
    # LetterRoom
    path("letterrooms/my", views.my_letterrooms),                          # GET (owner, sort=recent|dday_asc)
    path("letterrooms", views.create_letterroom),                          # POST
    path("letterrooms/<int:id>", views.delete_letterroom),                 # DELETE
    path("letterrooms/<int:id>/share-link", views.get_share_link),         # GET
    path("letterrooms/public/<str:share_code>", views.get_letterroom_by_sharecode),  # GET

    # RoomLetter
    path("letterrooms/<int:id>/letters", views.letters_collection),        # GET 목록 / POST 작성
    path("letterrooms/<int:id>/letters/<int:letter_id>", views.letter_detail),       # GET 상세

    # 편지방 공유 링크
    path("letterrooms/public/<str:share_code>", views.get_letterroom_by_sharecode, name="letterroom_public"),
]