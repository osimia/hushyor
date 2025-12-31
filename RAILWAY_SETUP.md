# 🚂 Деплой Hushyor на Railway

## 📋 Шаг 1: Установка PostgreSQL локально

### Windows:

1. **Скачайте PostgreSQL:**
   - https://www.postgresql.org/download/windows/
   - Или через Chocolatey: `choco install postgresql`

2. **Установите и запустите:**
   - Запомните пароль для пользователя `postgres`
   - Порт по умолчанию: `5432`

3. **Создайте базу данных:**

```bash
# Откройте psql
psql -U postgres

# Создайте базу
CREATE DATABASE hushyor;
CREATE USER hushyor_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE hushyor TO hushyor_user;
\q
```

## 📋 Шаг 2: Настройка локального PostgreSQL

### Обновите `.env`:

```env
# Существующие переменные
VITE_SUPABASE_PROJECT_ID="kyuudsemctvnehnlxrcg"
VITE_SUPABASE_PUBLISHABLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
VITE_SUPABASE_URL="https://kyuudsemctvnehnlxrcg.supabase.co"

# Gemini API
GEMINI_API_KEY="AIzaSyD-plcKkHN0rw3RHoPrvsI7-vCRVMBnp4w"

# PostgreSQL локально
DATABASE_URL=postgresql://hushyor_user:your_password@localhost:5432/hushyor
```

## 📋 Шаг 3: Экспорт данных из SQLite

```bash
# 1. Экспортируем данные
python manage.py dumpdata core.Subject core.Topic core.Task --indent 2 > hushyor_data.json

# Или используйте команду
python manage.py export_data --output hushyor_data.json
```

## 📋 Шаг 4: Миграция на PostgreSQL

```bash
# 1. Применяем миграции (создаем таблицы)
python manage.py migrate

# 2. Импортируем данные
python manage.py loaddata hushyor_data.json

# 3. Создаем суперпользователя
python manage.py createsuperuser

# 4. Проверяем
python manage.py runserver
```

## 📋 Шаг 5: Подготовка к деплою на Railway

### 1. Установите Railway CLI:

```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# Или через npm
npm install -g @railway/cli
```

### 2. Войдите в Railway:

```bash
railway login
```

### 3. Создайте проект:

```bash
railway init
```

### 4. Добавьте PostgreSQL:

```bash
railway add -d postgres
```

### 5. Получите DATABASE_URL:

```bash
railway variables
# Скопируйте DATABASE_URL
```

### 6. Установите переменные окружения:

```bash
railway variables set DJANGO_ENV=production
railway variables set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
railway variables set GEMINI_API_KEY=AIzaSyD-plcKkHN0rw3RHoPrvsI7-vCRVMBnp4w
railway variables set ALLOWED_HOSTS=*.railway.app
railway variables set PYTHON_VERSION=3.11.0
```

## 📋 Шаг 6: Деплой

```bash
# 1. Коммитим все изменения
git add .
git commit -m "Prepare for Railway deployment"
git push

# 2. Деплоим на Railway
railway up

# 3. Применяем миграции на Railway
railway run python manage.py migrate

# 4. Импортируем данные на Railway
railway run python manage.py loaddata hushyor_data.json

# 5. Создаем суперпользователя на Railway
railway run python manage.py createsuperuser

# 6. Собираем статику
railway run python manage.py collectstatic --noinput
```

## 📋 Шаг 7: Открываем приложение

```bash
railway open
```

## 🔧 Альтернатива: Через веб-интерфейс Railway

1. **Зайдите на https://railway.app**
2. **Создайте новый проект**
3. **Deploy from GitHub repo**
4. **Выберите репозиторий `hushyor`**
5. **Добавьте PostgreSQL:**
   - New → Database → PostgreSQL
6. **Настройте переменные:**
   - Settings → Variables → Add:
   ```
   DJANGO_ENV=production
   SECRET_KEY=<generate-random>
   GEMINI_API_KEY=AIzaSyD-plcKkHN0rw3RHoPrvsI7-vCRVMBnp4w
   ALLOWED_HOSTS=*.railway.app
   PYTHON_VERSION=3.11.0
   ```
7. **Deploy автоматически запустится**
8. **После деплоя выполните:**
   ```bash
   railway run python manage.py migrate
   railway run python manage.py loaddata hushyor_data.json
   ```

## 📊 Проверка

```bash
# Логи
railway logs

# Подключение к БД
railway connect postgres

# Выполнение команд
railway run python manage.py shell
```

## 🔄 Обновление

```bash
git add .
git commit -m "Update"
git push

# Railway автоматически задеплоит
```

## 🆘 Troubleshooting

### Ошибка подключения к БД:

```bash
railway variables
# Проверьте DATABASE_URL
```

### Статические файлы не работают:

```bash
railway run python manage.py collectstatic --noinput
```

### Миграции не применились:

```bash
railway run python manage.py showmigrations
railway run python manage.py migrate --run-syncdb
```

## 📝 Полезные команды

```bash
# Открыть проект в браузере
railway open

# Посмотреть логи
railway logs

# Выполнить команду
railway run <command>

# Подключиться к БД
railway connect postgres

# Статус
railway status

# Удалить проект
railway delete
```

## 🎉 Готово!

Ваше приложение доступно по адресу:
`https://your-app.railway.app`
