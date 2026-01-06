"""
Health check и мониторинг endpoints
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Health check endpoint для мониторинга состояния приложения
    
    Проверяет:
    - Подключение к базе данных
    - Работу кэша
    - Общее состояние приложения
    
    Returns:
        JsonResponse: Статус здоровья приложения
    """
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Проверка базы данных
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = 'connected'
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
    
    # Проверка кэша
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'ok', 10)
        cache_value = cache.get(cache_key)
        if cache_value == 'ok':
            health_status['checks']['cache'] = 'working'
        else:
            health_status['checks']['cache'] = 'not working'
            health_status['status'] = 'degraded'
    except Exception as e:
        logger.error(f"Cache health check failed: {e}", exc_info=True)
        health_status['checks']['cache'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Определяем HTTP статус
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Readiness check - проверка готовности приложения принимать трафик
    
    Returns:
        JsonResponse: Статус готовности
    """
    try:
        # Проверка критичных компонентов
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'ready',
            'message': 'Application is ready to serve traffic'
        })
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return JsonResponse({
            'status': 'not ready',
            'error': str(e)
        }, status=503)


def liveness_check(request):
    """
    Liveness check - проверка что приложение живо
    
    Returns:
        JsonResponse: Статус жизнеспособности
    """
    return JsonResponse({
        'status': 'alive',
        'message': 'Application is running'
    })
