"""
API URL Configuration для мобильного приложения
Все маршруты начинаются с /api/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import (
    # Auth
    register_api,
    login_api,
    user_profile_api,
    
    # Home
    home_api,
    
    # ViewSets
    SubjectViewSet,
    TopicViewSet,
    TaskViewSet,
    
    # Progress
    user_progress_api,
    topic_progress_api,
    
    # Leaderboard & Stats
    leaderboard_api,
    user_stats_api,
)

# Router для ViewSets
router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    # ==================== Аутентификация ====================
    path('auth/register/', register_api, name='api_register'),
    path('auth/login/', login_api, name='api_login'),
    path('auth/profile/', user_profile_api, name='api_profile'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ==================== Главная ====================
    path('home/', home_api, name='api_home'),
    
    # ==================== Прогресс ====================
    path('progress/', user_progress_api, name='api_progress'),
    path('progress/topic/<int:topic_id>/', topic_progress_api, name='api_topic_progress'),
    
    # ==================== Leaderboard & Stats ====================
    path('leaderboard/', leaderboard_api, name='api_leaderboard'),
    path('stats/', user_stats_api, name='api_stats'),
    
    # ==================== ViewSets (subjects, topics, tasks) ====================
    path('', include(router.urls)),
]
