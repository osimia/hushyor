"""
Кастомные throttle классы для rate limiting
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoginRateThrottle(UserRateThrottle):
    """Ограничение попыток входа - 5 в час"""
    scope = 'login'


class AIRateThrottle(UserRateThrottle):
    """Ограничение AI запросов - 10 в час на пользователя"""
    scope = 'ai'
    
    def get_cache_key(self, request, view):
        """Создаем ключ кэша на основе IP для анонимов и user_id для авторизованных"""
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
