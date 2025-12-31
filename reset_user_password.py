import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User

# Находим пользователя
username = '992981022195'
new_password = '981022195Qaz'

try:
    user = User.objects.get(username=username)
    user.set_password(new_password)
    user.save()
    
    print(f"✅ Пароль успешно изменен для пользователя: {user.username}")
    print(f"   Имя: {user.first_name} {user.last_name}")
    print(f"   Новый пароль: {new_password}")
    print(f"\nТеперь вы можете войти с этими данными:")
    print(f"   Номер телефона: 992981022195")
    print(f"   Пароль: {new_password}")
    
except User.DoesNotExist:
    print(f"❌ Пользователь {username} не найден!")
