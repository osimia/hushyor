# 🚨 Критические проблемы проекта Hushyor

## ⚠️ ТОП-5 проблем, требующих немедленного внимания

### 1. 🧪 Полное отсутствие тестов (Критично!)

**Проблема:** В проекте нет ни одного теста. Файл `tests.py` пустой.

**Риски:**
- Невозможно гарантировать работоспособность после изменений
- Высокий риск регрессии при добавлении новых функций
- Сложно поддерживать и масштабировать проект

**Решение:**
```bash
# Установить pytest
pip install pytest pytest-django pytest-cov factory-boy

# Создать структуру тестов
mkdir -p core/tests
touch core/tests/__init__.py
touch core/tests/test_models.py
touch core/tests/test_api.py
touch core/tests/test_views.py

# Запустить тесты
pytest --cov=core --cov-report=html
```

**Минимальный пример теста:**
```python
# core/tests/test_models.py
import pytest
from django.contrib.auth.models import User
from core.models import Subject, Task, TaskAttempt

@pytest.mark.django_db
class TestTaskModel:
    def test_create_task(self):
        subject = Subject.objects.create(title="Математика")
        task = Task.objects.create(
            subject=subject,
            question="2+2=?",
            correct_answer="4"
        )
        assert task.question == "2+2=?"
        assert task.correct_answer == "4"
    
    def test_task_attempt(self):
        user = User.objects.create_user('test', 'test@test.com', 'pass')
        subject = Subject.objects.create(title="Математика")
        task = Task.objects.create(subject=subject, question="Test", correct_answer="1")
        
        attempt = TaskAttempt.objects.create(user=user, task=task)
        attempt.attempts = 1
        attempt.is_solved = True
        attempt.save()
        
        assert attempt.attempts == 1
        assert attempt.is_solved is True
```

---

### 2. ⚡ N+1 запросы к базе данных (Критично!)

**Проблема:** Множественные N+1 запросы во views и serializers.

**Примеры проблемных мест:**

**views.py, строка 24:**
```python
# ❌ ПЛОХО
subjects = Subject.objects.annotate(total_tasks=Count('tasks', distinct=True))
for subject in subjects:
    # Каждая итерация делает дополнительные запросы
    total = subject.total_tasks or 0
```

**views.py, строка 62:**
```python
# ❌ ПЛОХО
topics = Topic.objects.filter(subject=subject).prefetch_related('tasks')
for topic in topics:
    topic.completed_count = TaskAttempt.objects.filter(...).count()  # N+1!
```

**serializers.py, строка 60:**
```python
# ❌ ПЛОХО
def get_total_tasks(self, obj):
    return obj.tasks.count()  # Вызывается для каждого объекта!
```

**Решение:**
```python
# ✅ ХОРОШО - используем annotate
from django.db.models import Count, Q, Prefetch

# В views.py
subjects = Subject.objects.annotate(
    total_tasks=Count('tasks', distinct=True),
    completed_tasks=Count(
        'tasks',
        filter=Q(tasks__taskattempt__user=request.user, tasks__taskattempt__is_solved=True),
        distinct=True
    ) if request.user.is_authenticated else 0
)

# В serializers.py - использовать annotate в queryset ViewSet
class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return Subject.objects.annotate(
            total_tasks_count=Count('tasks')
        )

# В serializer
total_tasks = serializers.IntegerField(source='total_tasks_count', read_only=True)
```

**Как проверить:**
```bash
# Установить django-debug-toolbar
pip install django-debug-toolbar

# В settings.py добавить
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

---

### 3. 🔐 Отсутствие Rate Limiting (Критично!)

**Проблема:** Нет защиты от злоупотреблений API и брутфорс атак.

**Риски:**
- Возможность DDoS атак
- Брутфорс паролей
- Злоупотребление AI API (дорого!)
- Перегрузка сервера

**Уязвимые endpoints:**
- `/api/auth/login/` - можно брутфорсить пароли
- `/api/tasks/{id}/submit/` - можно спамить ответами
- AI endpoints - дорогие запросы к Gemini API

**Решение:**
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',      # 100 запросов в час для анонимов
        'user': '1000/hour',     # 1000 запросов в час для авторизованных
        'login': '5/hour',       # 5 попыток входа в час
        'ai': '10/hour',         # 10 AI запросов в час
    }
}

# Создать кастомные throttle классы
# core/throttling.py
from rest_framework.throttling import UserRateThrottle

class LoginRateThrottle(UserRateThrottle):
    scope = 'login'

class AIRateThrottle(UserRateThrottle):
    scope = 'ai'

# Применить к views
# api_views.py
from core.throttling import LoginRateThrottle, AIRateThrottle

@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_api(request):
    # ...

# views.py - для AI запросов
from django.core.cache import cache

def task_view(request, task_id):
    if 'theory' in request.POST or 'hint' in request.POST:
        # Проверка rate limit для AI
        user_key = f'ai_limit_{request.user.id if request.user.is_authenticated else request.META.get("REMOTE_ADDR")}'
        requests_count = cache.get(user_key, 0)
        
        if requests_count >= 10:  # Максимум 10 запросов в час
            return JsonResponse({
                'error': 'Превышен лимит AI запросов. Попробуйте через час.'
            }, status=429)
        
        cache.set(user_key, requests_count + 1, 3600)  # 1 час
```

---

### 4. 🐛 Плохая обработка ошибок (Критично!)

**Проблема:** Отсутствие обработки исключений, использование `.get()` без try-except.

**Примеры проблем:**

**views.py, строка 138:**
```python
# ❌ ПЛОХО - может вызвать DoesNotExist
task = Task.objects.get(id=task_id)
```

**views.py, строка 199:**
```python
# ❌ ПЛОХО - может вызвать DoesNotExist
profile = UserProfile.objects.get(user=request.user)
```

**ai_helper.py, строка 34:**
```python
# ❌ ПЛОХО - слишком общая обработка
except Exception as e:
    return f"Ошибка при генерации теории: {str(e)}"
```

**Решение:**
```python
# ✅ ХОРОШО - использовать get_object_or_404
from django.shortcuts import get_object_or_404

def task_view(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    # ...

# ✅ ХОРОШО - использовать get_or_create
profile, created = UserProfile.objects.get_or_create(user=request.user)

# ✅ ХОРОШО - специфичная обработка ошибок
from google.api_core import exceptions as google_exceptions
import logging

logger = logging.getLogger(__name__)

def get_theory_lesson(task_question, task_subject):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except google_exceptions.ResourceExhausted:
        logger.warning("Gemini API quota exceeded")
        return "⚠️ Превышен лимит запросов к AI. Попробуйте позже."
    except google_exceptions.InvalidArgument as e:
        logger.error(f"Invalid argument to Gemini API: {e}")
        return "⚠️ Ошибка в запросе к AI"
    except Exception as e:
        logger.error(f"Unexpected error in AI helper: {e}", exc_info=True)
        return "⚠️ Временная ошибка AI. Попробуйте позже."

# Создать кастомный exception handler для DRF
# core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is None:
        logger.error(
            f"Unhandled exception in {context['view'].__class__.__name__}: {exc}",
            exc_info=True,
            extra={'request': context['request']}
        )
        return Response({
            'error': 'Internal server error',
            'detail': str(exc) if settings.DEBUG else 'An unexpected error occurred'
        }, status=500)
    
    return response

# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
}
```

---

### 5. 📝 Отсутствие логирования (Критично!)

**Проблема:** Минимальное логирование, сложно отлаживать проблемы в production.

**Что не логируется:**
- Ошибки в views
- Попытки входа (успешные и неуспешные)
- AI запросы и ошибки
- Административные действия
- Изменения данных

**Решение:**
```python
# settings.py
import os

# Создать директорию для логов
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module} {funcName} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
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
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
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
            'filename': os.path.join(LOGS_DIR, 'django.log'),
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'errors.log'),
            'maxBytes': 1024 * 1024 * 15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'security.log'),
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
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Использование в коде
import logging
logger = logging.getLogger(__name__)

# В views.py
def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            # ...
            if user is not None:
                login(request, user)
                logger.info(f"User {user.username} logged in successfully from {request.META.get('REMOTE_ADDR')}")
                return redirect('/')
            else:
                logger.warning(f"Failed login attempt for phone {phone} from {request.META.get('REMOTE_ADDR')}")

# В api_views.py
def submit(self, request, pk=None):
    logger.info(f"User {request.user.id} submitting answer for task {pk}")
    try:
        # ...
        logger.info(f"Answer {'correct' if is_correct else 'incorrect'} for task {pk} by user {request.user.id}")
    except Exception as e:
        logger.error(f"Error submitting answer: {e}", exc_info=True)

# В ai_helper.py
def get_theory_lesson(task_question, task_subject):
    logger.info(f"AI theory request for subject: {task_subject}")
    try:
        # ...
        logger.info("AI theory generated successfully")
    except Exception as e:
        logger.error(f"AI error: {e}", exc_info=True)
```

---

## 🎯 План действий на первую неделю

### День 1-2: Тесты
- [ ] Установить pytest и зависимости
- [ ] Создать структуру тестов
- [ ] Написать тесты для моделей
- [ ] Написать тесты для основных API endpoints
- [ ] Достичь покрытия минимум 30%

### День 3: N+1 запросы
- [ ] Установить django-debug-toolbar
- [ ] Найти все N+1 запросы
- [ ] Исправить в main_view
- [ ] Исправить в subject_view
- [ ] Исправить в serializers

### День 4: Rate Limiting
- [ ] Настроить DRF throttling
- [ ] Добавить rate limiting для login
- [ ] Добавить rate limiting для AI
- [ ] Протестировать лимиты

### День 5: Обработка ошибок
- [ ] Заменить .get() на get_object_or_404
- [ ] Добавить try-except блоки
- [ ] Создать custom exception handler
- [ ] Улучшить обработку AI ошибок

### День 6-7: Логирование
- [ ] Настроить LOGGING в settings
- [ ] Добавить логирование в views
- [ ] Добавить логирование в API
- [ ] Добавить логирование безопасности
- [ ] Протестировать логи

---

## 📊 Ожидаемые результаты

После исправления этих 5 критических проблем:

✅ **Надежность:** Проект будет стабильнее благодаря тестам  
✅ **Производительность:** Запросы к БД будут в 5-10 раз быстрее  
✅ **Безопасность:** Защита от брутфорса и DDoS  
✅ **Отказоустойчивость:** Корректная обработка всех ошибок  
✅ **Мониторинг:** Возможность отслеживать проблемы в production  

---

**Приоритет:** 🔴 КРИТИЧЕСКИЙ  
**Срок:** 1 неделя  
**Создано:** 2026-01-06
