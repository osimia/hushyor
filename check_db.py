import os
import sys
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Загружаем переменные окружения из .env
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ")
print("=" * 60)

# Проверяем DATABASE_URL
database_url = os.getenv('DATABASE_URL')
print(f"\n1. DATABASE_URL установлен: {'✓ ДА' if database_url else '✗ НЕТ'}")
if database_url:
    # Скрываем пароль для безопасности
    safe_url = database_url.split('@')[1] if '@' in database_url else database_url
    print(f"   Подключение к: {safe_url}")
else:
    print("   ⚠ Используется SQLite (локальная разработка)")

# Проверяем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from django.conf import settings
from django.db import connection

print(f"\n2. Используемая БД: {settings.DATABASES['default']['ENGINE']}")
if 'postgresql' in settings.DATABASES['default']['ENGINE']:
    print(f"   Имя БД: {settings.DATABASES['default'].get('NAME', 'N/A')}")
    print(f"   Хост: {settings.DATABASES['default'].get('HOST', 'N/A')}")
    print(f"   Порт: {settings.DATABASES['default'].get('PORT', 'N/A')}")
    print(f"   Пользователь: {settings.DATABASES['default'].get('USER', 'N/A')}")
else:
    print(f"   Файл БД: {settings.DATABASES['default'].get('NAME', 'N/A')}")

# Пытаемся подключиться
print("\n3. Проверка подключения...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"   ✓ Подключение успешно!")
        if version:
            print(f"   Версия: {version[0][:50]}...")
        
        # Проверяем существующие таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"\n4. Найдено таблиц: {len(tables)}")
        if tables:
            print("   Существующие таблицы:")
            for table in tables[:10]:  # Показываем первые 10
                print(f"   - {table[0]}")
            if len(tables) > 10:
                print(f"   ... и еще {len(tables) - 10} таблиц")
        else:
            print("   ⚠ Таблицы не найдены. Нужно выполнить миграции!")
            print("\n   Выполните команду:")
            print("   python manage.py migrate")
            
except Exception as e:
    print(f"   ✗ Ошибка подключения: {e}")
    print("\n   Возможные причины:")
    print("   1. PostgreSQL не запущен")
    print("   2. Неверные учетные данные в .env")
    print("   3. База данных не создана")
    print("\n   Проверьте:")
    print("   - Запущен ли PostgreSQL")
    print("   - Правильность DATABASE_URL в .env файле")

print("\n" + "=" * 60)
