"""
Helper функции для уменьшения дублирования кода
"""
from django.core.cache import cache
from .models import UserProfile


def get_user_profile(user):
    """
    Безопасное получение или создание профиля пользователя
    
    Args:
        user: User объект
        
    Returns:
        UserProfile: Профиль пользователя
    """
    profile, created = UserProfile.objects.select_related('user').get_or_create(user=user)
    return profile


def get_client_ip(request):
    """
    Получение IP адреса клиента с учетом прокси
    
    Args:
        request: HTTP запрос
        
    Returns:
        str: IP адрес клиента
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def cache_key_for_user(prefix, user):
    """
    Создание ключа кэша для пользователя
    
    Args:
        prefix: Префикс ключа
        user: User объект или None
        
    Returns:
        str: Ключ кэша
    """
    if user and user.is_authenticated:
        return f"{prefix}_{user.id}"
    return f"{prefix}_anonymous"


def invalidate_user_cache(user, *prefixes):
    """
    Инвалидация кэша пользователя по префиксам
    
    Args:
        user: User объект
        *prefixes: Префиксы ключей кэша для удаления
    """
    for prefix in prefixes:
        cache_key = cache_key_for_user(prefix, user)
        cache.delete(cache_key)
