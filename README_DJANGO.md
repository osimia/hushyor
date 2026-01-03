# hushyor - Платформа для подготовки к ММТ

## Описание проекта
hushyor - это веб-приложение на Django для подготовки к ММТ (Межвузовское Мониторинговое Тестирование) в Таджикистане. Проект включает:
- Предметы и задания (Забони тоҷикӣ, География, Математика)
- AI-ассистент для помощи
- Профиль пользователя с отслеживанием прогресса
- Лидерборд
- Система авторизации
- REST API для мобильного приложения

## Технологии
- Python 3.12
- Django 6.0
- Django REST Framework 3.16.1
- PostgreSQL (продакшн) / SQLite3 (разработка)
- JWT Authentication
- CORS Headers
- TailwindCSS

## Быстрый старт

### 1. Клонирование репозитория
```bash
cd ~/Рабочий\ стол/projects/
git clone <repository-url> hushyor
cd hushyor
```

### 2. Создание и активация виртуального окружения

**Создание виртуального окружения:**
```bash
python3 -m venv my_env
```

**Активация виртуального окружения:**

Linux/Mac:
```bash
source my_env/bin/activate
```

Windows:
```bash
my_env\Scripts\activate
```

После активации вы увидите `(my_env)` в начале строки терминала.

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### 5. Применение миграций
```bash
python manage.py migrate
```

### 6. Создание суперпользователя
```bash
python manage.py createsuperuser
```

### 7. Импорт данных (опционально)
Если у вас есть fixture файлы с данными:
```bash
# Импорт данных таджикского языка
python3 import_tjk_data.py

# Импорт данных географии
python3 import_geography_data.py

# Или восстановить все данные сразу
python3 restore_all_data.py
```

### 8. Запуск сервера разработки
```bash
python manage.py runserver 127.0.0.1:8000
```

### 9. Открытие в браузере
- **Главная страница:** http://127.0.0.1:8000/
- **Админ-панель:** http://127.0.0.1:8000/hushyor-control-panel/

## Полезные команды

### Остановка сервера
Нажмите `Ctrl+C` в терминале

### Деактивация виртуального окружения
```bash
deactivate
```

### Повторный запуск после перезагрузки
```bash
cd ~/Рабочий\ стол/projects/hushyor
source my_env/bin/activate
python manage.py runserver 127.0.0.1:8000
```

### Создание миграций после изменения моделей
```bash
python manage.py makemigrations
python manage.py migrate
```

### Сбор статических файлов (для продакшна)
```bash
python manage.py collectstatic
```

## Тестовый пользователь
- Логин: `testuser`
- Пароль: `testpass123`

## Структура проекта
- `/` - Главная страница (список предметов)
- `/subject/<id>/` - Страница предмета (список заданий)
- `/task/<id>/` - Страница задания (решение, AI-ассистент)
- `/leaderboard/` - Лидерборд
- `/profile/` - Профиль пользователя
- `/login/` - Вход
- `/register/` - Регистрация
- `/admin/` - Админка Django

## API эндпоинты
- `/api/subjects/` - Предметы (CRUD)
- `/api/tasks/` - Задания (CRUD)
- `/api/leaderboard/` - Лидерборд (CRUD)
- `/api/profiles/` - Профили (CRUD)
- `/api/gmini/` - AI-ассистент (POST)

## Модели
- `Subject` - Предмет (название, иконка, цвет)
- `Task` - Задание (вопрос, варианты ответа, правильный ответ, сложность)
- `UserProfile` - Профиль пользователя (телефон, streak, XP)
- `Leaderboard` - Лидерборд (пользователь, очки)

## Разработка
Для добавления новых предметов и заданий используйте админку Django: http://127.0.0.1:8000/admin/
