import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import authenticate
from core.models import UserProfile

# Тестируем вход
phone = '992981022195'
password = '981022195Qaz'

print(f"🔍 Проверка входа для номера: {phone}")
print(f"=" * 50)

# Пробуем найти пользователя с номером (с + и без +)
user_profile = None
try:
    # Сначала пробуем точное совпадение
    user_profile = UserProfile.objects.get(phone=phone)
    print(f"✅ Найдено точное совпадение: {phone}")
except UserProfile.DoesNotExist:
    # Если не найдено, пробуем с + в начале
    try:
        user_profile = UserProfile.objects.get(phone=f'+{phone}')
        print(f"✅ Найдено с +: +{phone}")
    except UserProfile.DoesNotExist:
        # Если не найдено, пробуем без +
        try:
            user_profile = UserProfile.objects.get(phone=phone.lstrip('+'))
            print(f"✅ Найдено без +: {phone.lstrip('+')}")
        except UserProfile.DoesNotExist:
            pass

if user_profile:
    print(f"   User ID: {user_profile.user.id}")
    print(f"   Username: {user_profile.user.username}")
    print(f"   First name: {user_profile.user.first_name}")
    print(f"   Last name: {user_profile.user.last_name}")
    print(f"   Phone в профиле: {user_profile.phone}")
    print()
    
    # 2. Пробуем аутентифицировать
    username = user_profile.user.username
    print(f"🔐 Попытка аутентификации...")
    print(f"   Username для auth: {username}")
    print(f"   Password: {'*' * len(password)}")
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        print(f"✅ Аутентификация успешна!")
        print(f"   User: {user.username}")
        print(f"   Is active: {user.is_active}")
    else:
        print(f"❌ Аутентификация не удалась!")
        print(f"   Возможные причины:")
        print(f"   - Неверный пароль")
        print(f"   - Пользователь неактивен")
        
        # Проверяем статус пользователя
        print(f"\n📊 Статус пользователя:")
        print(f"   Is active: {user_profile.user.is_active}")
        print(f"   Has usable password: {user_profile.user.has_usable_password()}")
else:
    print(f"❌ Профиль с номером {phone} не найден!")
    print(f"\n📋 Список всех профилей:")
    for profile in UserProfile.objects.all():
        print(f"   - {profile.phone} (user: {profile.user.username})")
