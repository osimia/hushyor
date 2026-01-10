# Исправление Server Error 500 на Production

## Проблема
Страница тасков работает локально, но на сервере выдает Server Error 500.

## Причины
1. **Не скомпилированы переводы** - файлы `.mo` не создаются на сервере
2. **Отсутствует пакет gettext** для компиляции переводов
3. **Импорт AI helper может падать** если нет зависимостей

## Решения

### ✅ 1. Обновлен `nixpacks.toml`
```toml
[phases.setup]
nixPkgs = ['python311', 'postgresql', 'gettext']  # Добавлен gettext

[phases.build]
cmds = [
    'python manage.py compilemessages --ignore=venv --ignore=env',  # Компиляция переводов
    'python manage.py collectstatic --noinput',
    'python manage.py migrate --noinput'
]
```

### ✅ 2. Обновлен `Procfile`
```
release: python manage.py compilemessages --ignore=venv --ignore=env && python manage.py migrate
```

### ✅ 3. Добавлена обработка ошибок в `views.py`
- Импорт AI helper теперь с try/except
- Если импорт не удался, создаются заглушки
- Страница не падает, даже если AI недоступен

### ✅ 4. Обновлен `ALLOWED_HOSTS`
```python
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'hushyor.com', 'www.hushyor.com']
```

## Что делать дальше

1. **Закоммитить изменения:**
```bash
git add .
git commit -m "Fix: Add translation compilation and error handling for production"
git push
```

2. **Проверить переменные окружения на Railway:**
   - `GEMINI_API_KEY` - должен быть установлен
   - `SECRET_KEY` - должен быть установлен
   - `DJANGO_ENV=production` - опционально

3. **Проверить логи на Railway:**
```bash
railway logs
```

4. **Если все еще ошибка 500:**
   - Проверьте логи Railway для точной ошибки
   - Убедитесь что все зависимости из `requirements.txt` установлены
   - Проверьте что база данных доступна

## Проверка после деплоя
- [ ] Страница `/task/5568/` открывается
- [ ] Переводы работают (переключение языка)
- [ ] Кнопка "Изучить тему" работает
- [ ] Проверка ответов работает
