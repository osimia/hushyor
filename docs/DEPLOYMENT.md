# 🚀 Деплой Hushyor

## 📋 Конфигурация баз данных

Проект настроен для использования:
- **SQLite3** - локальная разработка
- **PostgreSQL** - продакшен

### Локальная разработка (SQLite)

По умолчанию используется SQLite. Просто запустите:

```bash
python manage.py migrate
python manage.py runserver
```

### Продакшен (PostgreSQL)

Настройка автоматически переключается на PostgreSQL при наличии переменной `DATABASE_URL`.

## 🔧 Переменные окружения

Создайте `.env` файл для продакшена:

```env
# Django
DJANGO_ENV=production
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Gemini API
GEMINI_API_KEY=your-gemini-api-key
```

## 📦 Установка зависимостей

```bash
pip install -r requirements.txt
```

### Зависимости включают:

- **Django** - веб-фреймворк
- **psycopg2-binary** - PostgreSQL адаптер
- **dj-database-url** - парсинг DATABASE_URL
- **gunicorn** - production WSGI сервер
- **whitenoise** - статические файлы
- **PyPDF2** - работа с PDF
- **Pillow** - обработка изображений

## 🗄️ Миграции базы данных

### Локально (SQLite):
```bash
python manage.py migrate
```

### На продакшене (PostgreSQL):
```bash
# Применить миграции
python manage.py migrate

# Собрать статические файлы
python manage.py collectstatic --noinput

# Создать суперпользователя
python manage.py createsuperuser
```

## 🌐 Деплой на Render.com

### 1. Создайте новый Web Service

- Подключите GitHub репозиторий
- Выберите ветку `main`

### 2. Настройки Build & Deploy

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start Command:**
```bash
gunicorn backend.wsgi:application
```

### 3. Environment Variables

Добавьте в Render:

```
DJANGO_ENV=production
SECRET_KEY=<generate-random-secret>
ALLOWED_HOSTS=your-app.onrender.com
DATABASE_URL=<render-postgresql-url>
GEMINI_API_KEY=<your-key>
PYTHON_VERSION=3.11.0
```

### 4. Создайте PostgreSQL базу

- В Render создайте PostgreSQL database
- Скопируйте Internal Database URL
- Добавьте как `DATABASE_URL` в Environment Variables

## 🌐 Деплой на Railway

### 1. Создайте новый проект

```bash
railway login
railway init
```

### 2. Добавьте PostgreSQL

```bash
railway add postgresql
```

### 3. Установите переменные

```bash
railway variables set DJANGO_ENV=production
railway variables set SECRET_KEY=your-secret-key
railway variables set ALLOWED_HOSTS=your-app.railway.app
railway variables set GEMINI_API_KEY=your-key
```

### 4. Деплой

```bash
railway up
```

## 🌐 Деплой на Heroku

### 1. Создайте приложение

```bash
heroku create hushyor
```

### 2. Добавьте PostgreSQL

```bash
heroku addons:create heroku-postgresql:mini
```

### 3. Установите переменные

```bash
heroku config:set DJANGO_ENV=production
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ALLOWED_HOSTS=hushyor.herokuapp.com
heroku config:set GEMINI_API_KEY=your-key
```

### 4. Создайте Procfile

```
web: gunicorn backend.wsgi:application
release: python manage.py migrate
```

### 5. Деплой

```bash
git push heroku main
```

## 🔒 Безопасность

В продакшене автоматически включаются:

- ✅ `DEBUG = False`
- ✅ `SECURE_SSL_REDIRECT = True`
- ✅ `SESSION_COOKIE_SECURE = True`
- ✅ `CSRF_COOKIE_SECURE = True`
- ✅ `SECURE_BROWSER_XSS_FILTER = True`
- ✅ `SECURE_CONTENT_TYPE_NOSNIFF = True`
- ✅ `X_FRAME_OPTIONS = 'DENY'`

## 📊 Импорт данных на продакшене

После деплоя импортируйте задания:

```bash
# Через SSH или Railway/Render CLI
python manage.py import_with_answers A2-12_Math_ru.pdf A2-12_Math_ru_key.pdf --subject "Математика"
```

## 🧪 Проверка

```bash
# Локально
python manage.py check --deploy

# Тест подключения к БД
python manage.py dbshell
```

## 📝 Логи

### Render:
```bash
# В веб-интерфейсе: Logs tab
```

### Railway:
```bash
railway logs
```

### Heroku:
```bash
heroku logs --tail
```

## 🔄 Обновление

```bash
git add .
git commit -m "Update"
git push origin main

# Деплой произойдет автоматически
```

## 🆘 Troubleshooting

### Ошибка подключения к БД

Проверьте `DATABASE_URL`:
```bash
echo $DATABASE_URL
```

### Статические файлы не загружаются

```bash
python manage.py collectstatic --noinput
```

### Миграции не применяются

```bash
python manage.py showmigrations
python manage.py migrate --run-syncdb
```
