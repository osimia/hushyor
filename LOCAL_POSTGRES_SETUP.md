# 🐘 Настройка локального PostgreSQL

## 📥 Установка PostgreSQL на Windows

### Вариант 1: Официальный установщик

1. **Скачайте:**
   - https://www.postgresql.org/download/windows/
   - Выберите последнюю версию (15.x или 16.x)

2. **Установите:**
   - Запустите установщик
   - Порт: `5432` (по умолчанию)
   - Пароль для `postgres`: запомните его!
   - Locale: `Russian, Russia` или `English, United States`

3. **Проверьте установку:**
   ```bash
   psql --version
   ```

### Вариант 2: Через Chocolatey

```bash
choco install postgresql
```

## 🗄️ Создание базы данных

### 1. Откройте psql:

```bash
psql -U postgres
```

Введите пароль, который установили при установке.

### 2. Создайте базу и пользователя:

```sql
-- Создаем базу данных
CREATE DATABASE hushyor;

-- Создаем пользователя
CREATE USER hushyor_user WITH PASSWORD 'hushyor_password_2024';

-- Даем права
ALTER DATABASE hushyor OWNER TO hushyor_user;
GRANT ALL PRIVILEGES ON DATABASE hushyor TO hushyor_user;

-- Выходим
\q
```

## 🔧 Настройка проекта

### 1. Обновите `.env`:

```env
# Существующие переменные
VITE_SUPABASE_PROJECT_ID="kyuudsemctvnehnlxrcg"
VITE_SUPABASE_PUBLISHABLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt5dXVkc2VtY3R2bmVobmx4cmNnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcxMjU1NzYsImV4cCI6MjA4MjcwMTU3Nn0.f911bad7O4sEoDek42y2l7ULXafwDvxlWEYChSpI_tQ"
VITE_SUPABASE_URL="https://kyuudsemctvnehnlxrcg.supabase.co"

# Gemini API Key
GEMINI_API_KEY="AIzaSyD-plcKkHN0rw3RHoPrvsI7-vCRVMBnp4w"

# PostgreSQL локально
DATABASE_URL=postgresql://hushyor_user:hushyor_password_2024@localhost:5432/hushyor
```

### 2. Проверьте подключение:

```bash
python manage.py dbshell
```

Если подключение успешно, вы увидите приглашение PostgreSQL.

## 📦 Миграция данных из SQLite

### Шаг 1: Экспорт из SQLite

```bash
# Убедитесь, что используете SQLite (закомментируйте DATABASE_URL в .env)
python manage.py dumpdata core.Subject core.Topic core.Task --indent 2 > hushyor_data.json
```

### Шаг 2: Переключение на PostgreSQL

Раскомментируйте `DATABASE_URL` в `.env`:

```env
DATABASE_URL=postgresql://hushyor_user:hushyor_password_2024@localhost:5432/hushyor
```

### Шаг 3: Создание таблиц

```bash
python manage.py migrate
```

### Шаг 4: Импорт данных

```bash
python manage.py loaddata hushyor_data.json
```

### Шаг 5: Создание суперпользователя

```bash
python manage.py createsuperuser
```

### Шаг 6: Проверка

```bash
python manage.py runserver
```

Откройте http://localhost:8000 и проверьте, что все данные на месте.

## ✅ Проверка данных

```bash
# Подключитесь к БД
psql -U hushyor_user -d hushyor

# Проверьте таблицы
\dt

# Проверьте количество записей
SELECT COUNT(*) FROM core_subject;
SELECT COUNT(*) FROM core_topic;
SELECT COUNT(*) FROM core_task;

# Выход
\q
```

## 🔄 Переключение между SQLite и PostgreSQL

### Использовать SQLite:

Закомментируйте в `.env`:
```env
# DATABASE_URL=postgresql://...
```

### Использовать PostgreSQL:

Раскомментируйте в `.env`:
```env
DATABASE_URL=postgresql://hushyor_user:hushyor_password_2024@localhost:5432/hushyor
```

## 🆘 Troubleshooting

### Ошибка: "password authentication failed"

```bash
# Проверьте пароль в .env
# Или сбросьте пароль:
psql -U postgres
ALTER USER hushyor_user WITH PASSWORD 'new_password';
\q
```

### Ошибка: "database does not exist"

```bash
psql -U postgres
CREATE DATABASE hushyor;
\q
```

### Ошибка: "could not connect to server"

```bash
# Проверьте, запущен ли PostgreSQL
# Windows:
services.msc
# Найдите "postgresql-x64-15" и запустите
```

### Ошибка при импорте данных

```bash
# Очистите БД и попробуйте снова
python manage.py flush
python manage.py migrate
python manage.py loaddata hushyor_data.json
```

## 📊 Полезные команды PostgreSQL

```bash
# Список баз данных
psql -U postgres -c "\l"

# Список таблиц
psql -U hushyor_user -d hushyor -c "\dt"

# Размер базы данных
psql -U hushyor_user -d hushyor -c "SELECT pg_size_pretty(pg_database_size('hushyor'));"

# Бэкап базы
pg_dump -U hushyor_user hushyor > backup.sql

# Восстановление
psql -U hushyor_user hushyor < backup.sql
```

## 🎉 Готово!

Теперь вы используете PostgreSQL локально, и данные готовы к деплою на Railway!
