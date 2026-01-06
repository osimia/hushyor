# 📚 Руководство по импорту тестов в базу данных

## 📊 Структура данных

### Модель Question (tojiki/models.py)

```python
class Question(models.Model):
    # Основные поля
    category = models.CharField(max_length=200)  # Категория теста
    question_text = models.TextField()           # Текст вопроса
    
    # Варианты ответов
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    
    # Правильный ответ
    correct_answer = models.CharField(max_length=1, choices=[
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')
    ])
    
    # Дополнительные поля
    is_poetry = models.BooleanField(default=False)  # Содержит ли поэзию
    
    # Поля для matching вопросов (сопоставление)
    matching_left_1 = models.TextField(blank=True)
    matching_left_2 = models.TextField(blank=True)
    matching_left_3 = models.TextField(blank=True)
    matching_left_4 = models.TextField(blank=True)
    matching_right_a = models.TextField(blank=True)
    matching_right_b = models.TextField(blank=True)
    matching_right_c = models.TextField(blank=True)
    matching_right_d = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## 📁 Подготовленные файлы

### 1. `test_database_clean.json` 
- Очищенные тесты без правильных ответов
- Всего: **1174 теста**

### 2. `answer_keys.json`
- Правильные ответы для тестов
- Всего: **907 ответов**
- ⚠️ **15 тестов без ответов**: 52, 81, 203, 234, 359, 390, 515, 546, 671, 702, 827, 858

### 3. `tests_for_import.json` ✅
- **ГОТОВЫЙ ФАЙЛ ДЛЯ ИМПОРТА В БД**
- Формат: Django fixtures
- Объединены тесты + правильные ответы

## 📊 Статистика по категориям

| Категория | Количество |
|-----------|------------|
| ЛЕКСИКА. ФРАЗЕОЛОГИЯ | 781 |
| ИМЛО. ЛЕКСИКА. ФРАЗЕОЛОГИЯ | 230 |
| САВОЛУ МАСЪАЛАҲО БО ИНТИХОБИ ЯК ҶАВОБИ ДУРУСТ | 138 |
| НАМУНАИ СУБТЕСТИ ЗАБОНИ ТОҶИКӢ | 25 |

## 🚀 Импорт в базу данных

### Способ 1: Django loaddata (рекомендуется)

```bash
# 1. Перейдите в директорию проекта Django
cd /path/to/django/project

# 2. Импортируйте данные
python manage.py loaddata /home/osimi/Рабочий\ стол/projects/hushyor/tests_for_import.json

# 3. Проверьте импорт
python manage.py shell
>>> from tojiki.models import Question
>>> Question.objects.count()
1174
```

### Способ 2: Кастомная команда Django

Создайте файл `tojiki/management/commands/import_tests.py`:

```python
from django.core.management.base import BaseCommand
from tojiki.models import Question
import json

class Command(BaseCommand):
    help = 'Импорт тестов из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        with open(options['json_file'], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            Question.objects.update_or_create(
                id=item['pk'],
                defaults=item['fields']
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Успешно импортировано {len(data)} тестов')
        )
```

Запуск:
```bash
python manage.py import_tests tests_for_import.json
```

### Способ 3: Python скрипт

```python
import json
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from tojiki.models import Question

with open('tests_for_import.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    Question.objects.update_or_create(
        id=item['pk'],
        defaults=item['fields']
    )

print(f"Импортировано: {Question.objects.count()} тестов")
```

## 📝 Пример записи в БД

```json
{
  "model": "tojiki.question",
  "pk": 1,
  "fields": {
    "category": "САВОЛУ МАСЪАЛАҲО БО ИНТИХОБИ ЯК ҶАВОБИ ДУРУСТ",
    "question_text": "Дар кадом калима зада дар ҳиҷои аввал меояд?",
    "option_a": "саҳро",
    "option_b": "имрӯз",
    "option_c": "берун",
    "option_d": "сӯзан",
    "correct_answer": "D",
    "is_poetry": false,
    "matching_left_1": "",
    "matching_left_2": "",
    "matching_left_3": "",
    "matching_left_4": "",
    "matching_right_a": "",
    "matching_right_b": "",
    "matching_right_c": "",
    "matching_right_d": ""
  }
}
```

## ⚠️ Важные замечания

1. **Тесты без ответов**: 15 тестов имеют `correct_answer: null`
2. **Matching вопросы**: Поля для сопоставления заполнены только у специальных вопросов
3. **Кодировка**: Все файлы в UTF-8
4. **ID тестов**: Сохранены оригинальные ID (1-919)

## 🔍 Проверка после импорта

```python
# Django shell
python manage.py shell

# Проверки
from tojiki.models import Question

# Общее количество
Question.objects.count()  # Должно быть 1174

# Тесты без ответов
Question.objects.filter(correct_answer__isnull=True).count()  # 15

# По категориям
Question.objects.values('category').annotate(count=Count('id'))

# Случайный тест
Question.objects.order_by('?').first()
```

## 🛠️ Повторная подготовка данных

Если нужно перегенерировать файл импорта:

```bash
python3 prepare_db_import.py
```

Скрипт:
- Читает `test_database_clean.json`
- Читает `answer_keys.json`
- Объединяет данные
- Создает `tests_for_import.json`

## 📞 Поддержка

При проблемах с импортом проверьте:
- ✅ Миграции применены: `python manage.py migrate`
- ✅ Модель Question существует в `tojiki/models.py`
- ✅ Путь к файлу корректный
- ✅ Кодировка UTF-8
