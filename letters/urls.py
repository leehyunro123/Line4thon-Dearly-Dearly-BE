# directletters/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_direct_letter),          # POST
    path("inbox/", views.direct_letter_inbox),     # GET 목록
    path("self/", views.self_letter_inbox),  
    path("<int:id>/", views.direct_letter_detail), # GET 상세
]
