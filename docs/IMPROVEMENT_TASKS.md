# 📋 Задачи по улучшению проекта Hushyor

## 🔴 Критические задачи (выполнить в первую очередь)

### 1. Добавить тесты
**Приоритет:** Критический  
**Время:** 2-3 дня  
**Файлы:** `core/tests/`

**Задачи:**
- [ ] Создать структуру тестов
- [ ] Написать тесты для моделей (test_models.py)
- [ ] Написать тесты для API (test_api.py)
- [ ] Написать тесты для views (test_views.py)
- [ ] Настроить pytest и coverage
- [ ] Достичь покрытия минимум 50%

**Команды:**
```bash
pip install pytest pytest-django pytest-cov factory-boy
pytest --cov=core --cov-report=html
```

---

### 2. Исправить N+1 запросы
**Приоритет:** Критический  
**Время:** 1 день  
**Файлы:** `core/views.py`, `core/api_views.py`, `core/serializers.py`

**Проблемные места:**
- [ ] `views.py:24` - main_view
- [ ] `views.py:62` - subject_view
- [ ] `views.py:238` - task_view
- [ ] `api_views.py:126` - home_api
- [ ] `serializers.py:60` - TopicDetailSerializer

**Решение:**
```python
# Использовать select_related и prefetch_related
subjects = Subject.objects.select_related('...').prefetch_related('...')

# Использовать annotate для подсчетов
subjects = Subject.objects.annotate(
    total_tasks=Count('tasks'),
    completed_tasks=Count('tasks', filter=Q(tasks__taskattempt__is_solved=True))
)
```

---

### 3. Добавить Rate Limiting
**Приоритет:** Критический  
**Время:** 4 часа  
**Файлы:** `backend/settings.py`, `core/api_views.py`

**Задачи:**
- [ ] Установить django-ratelimit
- [ ] Настроить throttling в DRF
- [ ] Добавить rate limiting для AI запросов
- [ ] Добавить rate limiting для login/register

**Код:**
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '5/hour',
    }
}

# api_views.py
from rest_framework.throttling import UserRateThrottle

class LoginRateThrottle(UserRateThrottle):
    rate = '5/hour'

@api_view(['POST'])
@throttle_classes([LoginRateThrottle])
def login_api(request):
    # ...
```

---

### 4. Улучшить обработку ошибок
**Приоритет:** Критический  
**Время:** 1 день  
**Файлы:** Все views и API

**Задачи:**
- [ ] Заменить все `.get()` на `get_object_or_404()`
- [ ] Добавить try-except блоки
- [ ] Создать кастомные exception handlers
- [ ] Добавить валидацию входных данных

**Код:**
```python
# core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is None:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return Response({
            'error': 'Internal server error',
            'detail': str(exc) if settings.DEBUG else 'An error occurred'
        }, status=500)
    
    return response

# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}
```

---

### 5. Настроить логирование
**Приоритет:** Критический  
**Время:** 2 часа  
**Файлы:** `backend/settings.py`

**Задачи:**
- [ ] Настроить LOGGING в settings.py
- [ ] Создать директорию logs/
- [ ] Добавить логирование во все критические места
- [ ] Настроить ротацию логов

**Код в settings.py:**
```python
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'maxBytes': 1024 * 1024 * 15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

---

## 🟡 Важные задачи (выполнить в ближайшее время)

### 6. Создать сервисный слой
**Приоритет:** Высокий  
**Время:** 2-3 дня  
**Файлы:** Новые файлы в `core/services/`

**Структура:**
```
core/
  services/
    __init__.py
    auth_service.py
    task_service.py
    progress_service.py
    leaderboard_service.py
    ai_service.py
```

**Задачи:**
- [ ] Создать TaskService для работы с задачами
- [ ] Создать ProgressService для прогресса
- [ ] Создать LeaderboardService
- [ ] Перенести логику из views в сервисы
- [ ] Обновить views для использования сервисов

**Пример TaskService:**
```python
# core/services/task_service.py
from django.db import transaction
from core.models import Task, TaskAttempt, UserProfile, Leaderboard
import logging

logger = logging.getLogger(__name__)

class TaskService:
    """Сервис для работы с задачами"""
    
    @staticmethod
    @transaction.atomic
    def submit_answer(user, task, answer):
        """
        Обработка ответа на задачу
        
        Args:
            user: User объект
            task: Task объект
            answer: строка с ответом
            
        Returns:
            tuple: (attempt, is_correct, points_earned)
        """
        try:
            attempt, created = TaskAttempt.objects.select_for_update().get_or_create(
                user=user,
                task=task
            )
            
            attempt.attempts += 1
            is_correct = str(answer).strip() == str(task.correct_answer).strip()
            points_earned = 0
            
            if is_correct and not attempt.is_solved:
                points_earned = TaskService._calculate_points(task, attempt)
                TaskService._award_points(user, points_earned)
                attempt.is_solved = True
                attempt.points_earned = points_earned
            
            attempt.save()
            logger.info(f"User {user.id} submitted answer for task {task.id}: {'correct' if is_correct else 'incorrect'}")
            
            return attempt, is_correct, points_earned
            
        except Exception as e:
            logger.error(f"Error submitting answer: {e}", exc_info=True)
            raise
    
    @staticmethod
    def _calculate_points(task, attempt):
        """Расчет очков за задачу"""
        base_points = task.difficulty * 5
        if attempt.attempts == 1:
            return base_points
        elif attempt.attempts == 2:
            return int(base_points * 0.7)
        else:
            return int(base_points * 0.5)
    
    @staticmethod
    def _award_points(user, points):
        """Начисление очков пользователю"""
        profile = UserProfile.objects.select_for_update().get(user=user)
        profile.xp += points
        profile.save()
        
        leaderboard, _ = Leaderboard.objects.get_or_create(user_profile=profile)
        leaderboard.points = profile.xp
        leaderboard.save()
```

---

### 7. Добавить кэширование
**Приоритет:** Высокий  
**Время:** 1-2 дня  
**Файлы:** `backend/settings.py`, все views

**Задачи:**
- [ ] Настроить Redis для кэширования
- [ ] Добавить кэширование для главной страницы
- [ ] Кэшировать список предметов
- [ ] Кэшировать leaderboard
- [ ] Кэшировать AI ответы
- [ ] Кэшировать OG изображения

**Настройка Redis:**
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'hushyor',
        'TIMEOUT': 300,
    }
}

# Кэш для сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

**Использование:**
```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# Кэширование view
@cache_page(60 * 5)  # 5 минут
def main_view(request):
    # ...

# Кэширование данных
def get_subjects():
    cache_key = 'subjects_list'
    subjects = cache.get(cache_key)
    
    if subjects is None:
        subjects = list(Subject.objects.all())
        cache.set(cache_key, subjects, 60 * 10)  # 10 минут
    
    return subjects

# Инвалидация кэша
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Subject)
def invalidate_subjects_cache(sender, instance, **kwargs):
    cache.delete('subjects_list')
```

---

### 8. Настроить мониторинг (Sentry)
**Приоритет:** Высокий  
**Время:** 2 часа  
**Файлы:** `backend/settings.py`, `requirements.txt`

**Задачи:**
- [ ] Зарегистрироваться в Sentry
- [ ] Установить sentry-sdk
- [ ] Настроить интеграцию
- [ ] Протестировать отправку ошибок

**Код:**
```bash
pip install sentry-sdk
```

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production' if _is_production else 'development',
    )
```

---

### 9. Добавить API документацию
**Приоритет:** Высокий  
**Время:** 4 часа  
**Файлы:** `backend/settings.py`, `backend/urls.py`

**Задачи:**
- [ ] Установить drf-spectacular
- [ ] Настроить схему API
- [ ] Добавить описания к endpoints
- [ ] Создать Swagger UI

**Код:**
```bash
pip install drf-spectacular
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Hushyor API',
    'DESCRIPTION': 'API для образовательной платформы Hushyor',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

---

### 10. Оптимизировать запросы к БД
**Приоритет:** Высокий  
**Время:** 1 день  
**Файлы:** Все views и API

**Задачи:**
- [ ] Установить django-debug-toolbar
- [ ] Найти все медленные запросы
- [ ] Добавить индексы в модели
- [ ] Использовать only() и defer()
- [ ] Оптимизировать сложные запросы

**Установка debug toolbar:**
```bash
pip install django-debug-toolbar
```

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# urls.py
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

**Добавить индексы:**
```python
# models.py
class Task(models.Model):
    # ...
    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['subject', 'topic']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['order']),
            models.Index(fields=['subject', 'order']),
        ]

class TaskAttempt(models.Model):
    # ...
    class Meta:
        unique_together = ('user', 'task')
        indexes = [
            models.Index(fields=['user', 'is_solved']),
            models.Index(fields=['user', 'task', 'is_solved']),
            models.Index(fields=['-updated_at']),
        ]
```

---

## 🟢 Желательные задачи (можно отложить)

### 11. Разделить settings на окружения
**Приоритет:** Средний  
**Время:** 2 часа

**Структура:**
```
backend/
  settings/
    __init__.py
    base.py          # Общие настройки
    development.py   # Для разработки
    production.py    # Для продакшена
    testing.py       # Для тестов
```

---

### 12. Добавить pre-commit hooks
**Приоритет:** Средний  
**Время:** 1 час

**Задачи:**
- [ ] Установить pre-commit
- [ ] Настроить black, flake8, isort
- [ ] Добавить проверку перед коммитом

**Файл `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--ignore=E203,W503']

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile', 'black']
```

---

### 13. Настроить CI/CD
**Приоритет:** Средний  
**Время:** 4 часа

**Создать `.github/workflows/tests.yml`:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-django pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
      run: |
        pytest --cov=core --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

### 14. Добавить type hints
**Приоритет:** Низкий  
**Время:** 2-3 дня

**Пример:**
```python
from typing import Optional, List, Tuple
from django.contrib.auth.models import User
from core.models import Task, TaskAttempt

def submit_answer(
    user: User, 
    task: Task, 
    answer: str
) -> Tuple[TaskAttempt, bool, int]:
    """
    Обработка ответа на задачу
    
    Args:
        user: Пользователь
        task: Задача
        answer: Ответ пользователя
        
    Returns:
        Кортеж (попытка, правильность, очки)
    """
    # ...
```

---

### 15. Улучшить структуру проекта
**Приоритет:** Низкий  
**Время:** 1-2 дня

**Новая структура:**
```
core/
  api/
    __init__.py
    views.py
    serializers.py
    urls.py
  services/
    __init__.py
    task_service.py
    progress_service.py
    auth_service.py
  utils/
    __init__.py
    cache.py
    validators.py
  tests/
    __init__.py
    test_models.py
    test_api.py
    test_services.py
```

---

## 📊 Чек-лист выполнения

### Неделя 1: Критические задачи
- [ ] Задача 1: Добавить тесты
- [ ] Задача 2: Исправить N+1 запросы
- [ ] Задача 3: Добавить Rate Limiting
- [ ] Задача 4: Улучшить обработку ошибок
- [ ] Задача 5: Настроить логирование

### Неделя 2: Важные задачи
- [ ] Задача 6: Создать сервисный слой
- [ ] Задача 7: Добавить кэширование
- [ ] Задача 8: Настроить мониторинг
- [ ] Задача 9: Добавить API документацию
- [ ] Задача 10: Оптимизировать запросы

### Неделя 3: Желательные задачи
- [ ] Задача 11: Разделить settings
- [ ] Задача 12: Добавить pre-commit hooks
- [ ] Задача 13: Настроить CI/CD
- [ ] Задача 14: Добавить type hints
- [ ] Задача 15: Улучшить структуру

---

## 🎯 Метрики успеха

После выполнения всех задач проект должен достичь:

- ✅ **Покрытие тестами:** минимум 70%
- ✅ **Производительность:** все запросы < 100ms
- ✅ **Безопасность:** A+ на security scanners
- ✅ **Документация:** 100% API endpoints документированы
- ✅ **Качество кода:** 0 критических замечаний от линтеров
- ✅ **Мониторинг:** все ошибки логируются в Sentry

---

**Создано:** 2026-01-06  
**Автор:** AI Code Reviewer
