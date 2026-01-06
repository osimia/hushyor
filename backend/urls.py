"""
URL configuration for backend project.

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
from rest_framework.routers import DefaultRouter
from core import views

router = DefaultRouter()
router.register(r'subjects', views.SubjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'leaderboard', views.LeaderboardViewSet)
router.register(r'profiles', views.UserProfileViewSet)

urlpatterns = [
    # ==================== SEO ====================
    path('sitemap.xml', views.sitemap_view, name='sitemap'),
    path('robots.txt', views.robots_txt_view, name='robots'),
    path('yandex_f58006ecd2f5e538.html', views.yandex_verification_view, name='yandex_verification'),
    
    # ==================== HTML Views (существующий сайт) ====================
    path('', views.main_view, name='main'),
    path('subject/<int:subject_id>/', views.subject_view, name='subject'),
    path('topic/<int:topic_id>/', views.topic_view, name='topic'),
    path('task/<int:task_id>/', views.task_view, name='task'),
    path('task/<int:task_id>/og-image.png', views.task_og_image_view, name='task_og_image'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('profile/', views.profile_view, name='profile'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset-confirm/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('admin-password-reset/', views.admin_password_reset_view, name='admin_password_reset'),
    path('hushyor-control-panel/', admin.site.urls),
    
    # ==================== API для мобильного приложения ====================
    path('api/v1/', include('core.urls_api')),  # Новый API для Flutter
    
    # ==================== Старый API (совместимость) ====================
    path('api/gmini/', views.gmini_api, name='gmini-api'),
    path('api/', include(router.urls)),
]
