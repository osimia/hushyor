from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re


class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма регистрации с поддержкой кириллицы"""
    
    full_name = forms.CharField(
        max_length=150,
        required=True,
        label='ФИО',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground',
            'placeholder': 'Введите ваше имя'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        label='Номер телефона',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground',
            'placeholder': '+998'
        })
    )
    
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground',
            'placeholder': '••••••••'
        })
    )
    
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground',
            'placeholder': '••••••••'
        })
    )
    
    class Meta:
        model = User
        fields = ('full_name', 'phone', 'password1', 'password2')
    
    def clean_full_name(self):
        """Валидация ФИО - разрешаем кириллицу, латиницу, пробелы, дефисы"""
        full_name = self.cleaned_data.get('full_name')
        
        # Проверяем, что имя содержит только разрешенные символы
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', full_name):
            raise ValidationError('ФИО может содержать только буквы, пробелы и дефисы')
        
        # Проверяем минимальную длину
        if len(full_name.strip()) < 2:
            raise ValidationError('ФИО должно содержать минимум 2 символа')
        
        return full_name.strip()
    
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        # Убираем все символы кроме цифр и +
        phone_cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Проверяем формат
        if not re.match(r'^\+?\d{10,15}$', phone_cleaned):
            raise ValidationError('Введите корректный номер телефона')
        
        # Проверяем уникальность
        from .models import UserProfile
        if UserProfile.objects.filter(phone=phone_cleaned).exists():
            raise ValidationError('Этот номер телефона уже зарегистрирован')
        
        return phone_cleaned
    
    def save(self, commit=True):
        """Создаем пользователя с username из телефона"""
        user = super().save(commit=False)
        
        # Используем телефон как username (уникальный идентификатор)
        phone = self.cleaned_data['phone']
        user.username = phone.replace('+', '').replace(' ', '')
        
        # Сохраняем ФИО в first_name и last_name
        full_name = self.cleaned_data['full_name']
        name_parts = full_name.split(maxsplit=1)
        user.first_name = name_parts[0] if len(name_parts) > 0 else ''
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if commit:
            user.save()
            
            # Создаем профиль пользователя
            from .models import UserProfile
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data['phone']
            )
        
        return user


class CustomLoginForm(forms.Form):
    """Форма входа по номеру телефона"""
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        label='Номер телефона',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground',
            'placeholder': '+998'
        })
    )
    
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-border bg-background text-foreground',
            'placeholder': '••••••••'
        })
    )
    
    def clean_phone(self):
        """Очищаем номер телефона"""
        phone = self.cleaned_data.get('phone')
        return re.sub(r'[^\d+]', '', phone)
