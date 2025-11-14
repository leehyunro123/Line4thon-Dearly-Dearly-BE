from django.urls import path
from . import views

urlpatterns = [
    path("notifications/", views.notification_list),
    path("notifications/<int:pk>/read/", views.notification_read),
]
