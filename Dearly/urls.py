"""
URL configuration for Dearly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # 하단 개발용 때매 필요
from django.conf.urls.static import static # 하단 개발용 떄매 필요
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Swagger API 문서
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # 앱 URL들
    path("", include("letterrooms.urls")),
    path("", include('users.urls')),
    path("", include('login.urls')),  # 로그인/인증 관련
    path("letters/", include("letters.urls")),
    path("friends/", include("friends.urls")),
    path("", include("notices.urls")),
    path("",include("notifications.urls")),
]

# 개발할때만 임시로 이미지 확인하려고 넣음 (배포하면 필요없음)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 