from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re


class CustomUserCreationForm(forms.Form):
    """Упрощенная форма регистрации - только телефон и пароль"""
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        label='Номер телефона',
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-28 pr-4 py-3.5 bg-muted border-2 border-transparent rounded-xl text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors text-lg',
            'placeholder': '90 123 45 67',
            'inputmode': 'tel',
            'autocomplete': 'tel',
            'autofocus': True,
            'id': 'phone'
        })
    )
    
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full pl-12 pr-12 py-3.5 bg-muted border-2 border-transparent rounded-xl text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors text-lg',
            'placeholder': 'Минимум 8 символов',
            'id': 'password1'
        })
    )
    
    def clean_password1(self):
        """Валидация пароля"""
        password = self.cleaned_data.get('password1')
        
        if len(password) < 8:
            raise ValidationError('Пароль должен содержать минимум 8 символов')
        
        return password
    
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        # Убираем все символы кроме цифр и +
        phone_cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Если номер не начинается с +, добавляем +992
        if not phone_cleaned.startswith('+'):
            phone_cleaned = '+992' + phone_cleaned
        
        # Проверяем формат
        if not re.match(r'^\+\d{10,15}$', phone_cleaned):
            raise ValidationError('Введите корректный номер телефона')
        
        # Проверяем уникальность
        from .models import UserProfile
        if UserProfile.objects.filter(phone=phone_cleaned).exists():
            raise ValidationError('Этот номер телефона уже зарегистрирован')
        
        return phone_cleaned
    
    def save(self, commit=True):
        """Создаем пользователя с username из телефона"""
        from .models import UserProfile
        
        phone = self.cleaned_data['phone']
        password = self.cleaned_data['password1']
        
        # Используем телефон как username (уникальный идентификатор)
        username = phone.replace('+', '').replace(' ', '')
        
        # Генерируем уникальное имя пользователя
        user_count = User.objects.count() + 1
        display_name = f'user_{user_count}'
        
        # Создаем пользователя
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=display_name,
            last_name=''
        )
        
        if commit:
            # Создаем профиль пользователя
            UserProfile.objects.create(
                user=user,
                phone=phone
            )
        
        return user


class CustomLoginForm(forms.Form):
    """Форма входа по номеру телефона"""
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        label='Номер телефона',
        widget=forms.TextInput(attrs={
            'class': 'w-full pl-28 pr-4 py-3.5 bg-muted border-2 border-transparent rounded-xl text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors text-lg',
            'placeholder': '90 123 45 67',
            'inputmode': 'tel',
            'autocomplete': 'tel',
            'autofocus': True,
            'id': 'phone'
        })
    )
    
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full pl-12 pr-12 py-3.5 bg-muted border-2 border-transparent rounded-xl text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none transition-colors text-lg',
            'placeholder': '••••••••',
            'id': 'password'
        })
    )
    
    def clean_phone(self):
        """Очищаем номер телефона"""
        phone = self.cleaned_data.get('phone')
        phone_cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Если номер не начинается с +, добавляем +992
        if not phone_cleaned.startswith('+'):
            phone_cleaned = '+992' + phone_cleaned
        
        return phone_cleaned
