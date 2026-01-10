web: gunicorn backend.wsgi:application
release: python manage.py compilemessages --ignore=venv --ignore=env && python manage.py migrate
