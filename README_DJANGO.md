# PrepMate - Платформа для подготовки к ЕГЭ

## Описание проекта
PrepMate - это веб-приложение на Django для подготовки к экзаменам. Проект включает:
- Предметы и задания
- AI-ассистент для помощи
- Профиль пользователя с отслеживанием прогресса
- Лидерборд
- Система авторизации

## Технологии
- Python 3.x
- Django 5.2.9
- Django REST Framework 3.16.1
- SQLite3
- Bootstrap 5.3.2 (через CDN)

## Установка и запуск

1. Создайте виртуальное окружение:
```bash
python -m venv backend_env
```

2. Активируйте виртуальное окружение:
- Windows: `backend_env\Scripts\activate`
- Linux/Mac: `source backend_env/bin/activate`

3. Установите зависимости:
```bash
pip install django djangorestframework
```

4. Примените миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Создайте суперпользователя для админки:
```bash
python manage.py createsuperuser
```

6. Создайте тестовые данные:
```bash
python manage.py create_test_data
```

7. Запустите сервер:
```bash
python manage.py runserver
```

8. Откройте в браузере: http://127.0.0.1:8000/

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
