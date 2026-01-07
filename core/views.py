from django.shortcuts import render, redirect, get_object_or_404
from .models import Subject
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Subject, Task, UserProfile, Leaderboard
from django.contrib.auth.models import User

from .serializers import SubjectSerializer, TaskSerializer, UserProfileSerializer, LeaderboardSerializer

# Django view для главной страницы
from django.views import View
from django.shortcuts import render

def main_view(request):
    from .models import Task, TaskAttempt
    from django.db.models import Count, Q
    
    # Оптимизированный запрос с annotate для устранения N+1
    if request.user.is_authenticated:
        subjects = Subject.objects.annotate(
            total_tasks=Count('tasks', distinct=True),
            completed_tasks=Count(
                'tasks',
                filter=Q(tasks__taskattempt__user=request.user, tasks__taskattempt__is_solved=True),
                distinct=True
            )
        )
    else:
        subjects = Subject.objects.annotate(
            total_tasks=Count('tasks', distinct=True)
        )

    # Добавляем информацию о прогрессе к каждому предмету
    subjects_with_progress = []
    for subject in subjects:
        total = subject.total_tasks or 0
        completed = subject.completed_tasks if request.user.is_authenticated else 0
        percentage = int((completed / total) * 100) if total > 0 else 0

        subject.completed = completed
        subject.total = total
        subject.percentage = percentage
        subjects_with_progress.append(subject)
    
    # Статистика для главной страницы (кэшируем на 5 минут)
    from django.core.cache import cache
    stats = cache.get('main_stats')
    if stats is None:
        stats = {
            'total_users': User.objects.count(),
            'total_tasks': Task.objects.count(),
            'total_subjects': Subject.objects.count(),
        }
        cache.set('main_stats', stats, 300)  # 5 минут
    
    return render(request, 'main.html', {
        'subjects': subjects_with_progress,
        'stats': stats
    })

def subject_view(request, subject_id):
    from .models import Task, Topic, UserProgress, TaskAttempt
    from django.db.models import Prefetch
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Оптимизированная загрузка тем с задачами
    topics = Topic.objects.filter(subject=subject).prefetch_related(
        Prefetch('tasks', queryset=Task.objects.only('id', 'topic_id', 'order'))
    )
    
    # Получаем все решенные задачи одним запросом
    solved_task_ids = set()
    if request.user.is_authenticated:
        solved_task_ids = set(
            TaskAttempt.objects.filter(
                user=request.user,
                task__subject=subject,
                is_solved=True
            ).values_list('task_id', flat=True)
        )
    
    # Calculate progress for each topic
    total_completed = 0
    for topic in topics:
        topic.total_count = topic.tasks.count()
        
        # Подсчет решенных задач из предзагруженного набора
        if request.user.is_authenticated:
            topic.completed_count = sum(1 for task in topic.tasks.all() if task.id in solved_task_ids)
            total_completed += topic.completed_count
        else:
            topic.completed_count = 0
        
        topic.progress_dots = range(min(topic.total_count, 4))  # Show max 4 dots
        topic.is_completed = (topic.completed_count == topic.total_count and topic.total_count > 0)
    
    # Calculate overall progress
    total_tasks = Task.objects.filter(subject=subject).count()
    progress_percentage = int((total_completed / total_tasks * 100)) if total_tasks > 0 else 0
    
    context = {
        'subject': subject,
        'topics': topics,
        'total_items': topics.count(),
        'total_tasks': total_tasks,
        'completed_tasks': total_completed,
        'progress_percentage': progress_percentage,
    }
    return render(request, 'subject.html', context)

def topic_view(request, topic_id):
    from .models import Task, Topic, TaskAttempt
    topic = Topic.objects.get(id=topic_id)
    tasks = Task.objects.filter(topic=topic).order_by('order')
    
    # Redirect to first task if tasks exist
    if tasks.exists():
        if request.user.is_authenticated:
            # 1) Продолжаем с последней открытой задачи в этой теме
            last_attempt = (
                TaskAttempt.objects
                .filter(user=request.user, task_id__in=tasks.values_list('id', flat=True))
                .select_related('task')
                .order_by('-updated_at')
                .first()
            )
            if last_attempt and not last_attempt.is_solved:
                return redirect(f'/task/{last_attempt.task.id}/')

            # 2) Если последняя открытая задача решена — переходим на первую нерешённую
            solved_task_ids = set(
                TaskAttempt.objects.filter(
                    user=request.user,
                    task_id__in=tasks.values_list('id', flat=True),
                    is_solved=True,
                ).values_list('task_id', flat=True)
            )
            unsolved_tasks = tasks.exclude(id__in=solved_task_ids)
            if unsolved_tasks.exists():
                return redirect(f'/task/{unsolved_tasks.first().id}/')
        first_task = tasks.first()
        return redirect(f'/task/{first_task.id}/')
    else:
        # No tasks, redirect back to subject
        return redirect(f'/subject/{topic.subject.id}/')

def task_view(request, task_id):
    from .models import Task, TaskAttempt, UserProfile, Leaderboard
    from .ai_helper import get_theory_lesson, get_hint, get_ai_response
    from django.http import JsonResponse
    import logging
    
    logger = logging.getLogger(__name__)
    
    task = get_object_or_404(Task.objects.select_related('subject', 'topic'), id=task_id)
    result = None
    ai_reply = None
    points_earned = 0
    attempt_info = None
    
    # Получаем или создаем запись о попытках для авторизованного пользователя
    if request.user.is_authenticated:
        attempt, created = TaskAttempt.objects.get_or_create(
            user=request.user,
            task=task
        )
        attempt_info = attempt
        logger.info(f"User {request.user.id} viewing task {task_id}")
    
    if request.method == 'POST':
        # Проверяем, это AJAX запрос или нет
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            # Проверка rate limit для AI запросов
            if 'theory' in request.POST or 'hint' in request.POST or 'ai_message' in request.POST:
                from django.core.cache import cache
                
                # Создаем ключ для rate limiting
                user_key = f'ai_limit_{request.user.id if request.user.is_authenticated else request.META.get("REMOTE_ADDR")}'
                requests_count = cache.get(user_key, 0)
                
                if requests_count >= 10:  # Максимум 10 AI запросов в час
                    logger.warning(f"AI rate limit exceeded for {user_key}")
                    if is_ajax:
                        return JsonResponse({
                            'error': 'Превышен лимит AI запросов. Попробуйте через час.'
                        }, status=429)
                    messages.error(request, 'Превышен лимит AI запросов. Попробуйте через час.')
                    return redirect(f'/task/{task_id}/')
                
                # Увеличиваем счетчик
                cache.set(user_key, requests_count + 1, 3600)  # 1 час
            
            if 'theory' in request.POST:
                # Запрос теории
                logger.info(f"AI theory request for task {task_id} by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                ai_reply = get_theory_lesson(task.question, task.subject.title)
                if is_ajax:
                    return JsonResponse({'ai_reply': ai_reply})
            elif 'hint' in request.POST:
                # Запрос подсказки
                logger.info(f"AI hint request for task {task_id} by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
                ai_reply = get_hint(task.question, task.subject.title)
                if is_ajax:
                    return JsonResponse({'ai_reply': ai_reply})
            elif 'ai_message' in request.POST:
                # Произвольный вопрос к ИИ
                message = request.POST.get('ai_message', '').strip()
                if message and len(message) <= 500:  # Валидация длины
                    logger.info(f"AI custom question for task {task_id}")
                    ai_reply = get_ai_response(message, task.question, task.subject.title)
                    if is_ajax:
                        return JsonResponse({'ai_reply': ai_reply})
                elif is_ajax:
                    return JsonResponse({'error': 'Сообщение слишком длинное или пустое'}, status=400)
            else:
                # Проверка ответа
                answer = request.POST.get('answer', '').strip()
                
                # Валидация ответа
                if not answer:
                    if is_ajax:
                        return JsonResponse({'error': 'Ответ не может быть пустым'}, status=400)
                    messages.error(request, 'Ответ не может быть пустым')
                    return redirect(f'/task/{task_id}/')
                
                if len(answer) > 100:
                    if is_ajax:
                        return JsonResponse({'error': 'Ответ слишком длинный'}, status=400)
                    messages.error(request, 'Ответ слишком длинный')
                    return redirect(f'/task/{task_id}/')
                
                is_correct = (answer == task.correct_answer)
                result = is_correct
                
                logger.info(f"User {request.user.id if request.user.is_authenticated else 'anonymous'} submitted answer for task {task_id}: {'correct' if is_correct else 'incorrect'}")
                
                # Обработка попыток и начисление очков для авторизованных пользователей
                if request.user.is_authenticated and attempt_info:
                    if not attempt_info.is_solved:
                        attempt_info.attempts += 1
                        
                        if is_correct:
                            # Задача решена правильно
                            attempt_info.is_solved = True
                            
                            # Начисление очков: 100% за первую попытку, 50% за последующие
                            base_points = task.difficulty * 5  # 5 очков за уровень сложности
                            if attempt_info.attempts == 1:
                                points_earned = base_points
                            else:
                                points_earned = base_points // 2  # Половина очков
                            
                            attempt_info.points_earned = points_earned
                            
                            # Обновляем профиль пользователя
                            try:
                                profile, created = UserProfile.objects.get_or_create(user=request.user)
                                profile.xp += points_earned
                                profile.save()
                                
                                # Обновляем таблицу лидеров
                                leaderboard, _ = Leaderboard.objects.get_or_create(user_profile=profile)
                                leaderboard.points = profile.xp
                                leaderboard.save()
                                
                                logger.info(f"Awarded {points_earned} points to user {request.user.id}")
                            except Exception as e:
                                logger.error(f"Error awarding points: {e}", exc_info=True)
                        
                        attempt_info.save()
                
                # Если это AJAX запрос, возвращаем JSON
                if is_ajax:
                    # Находим следующую задачу
                    next_task_id = None
                    if task.topic:
                        topic_tasks = Task.objects.filter(topic=task.topic).order_by('order')
                        task_list = list(topic_tasks)
                        try:
                            current_index = task_list.index(task)
                            if current_index < len(task_list) - 1:
                                next_task_id = task_list[current_index + 1].id
                        except ValueError:
                            pass
                    
                    return JsonResponse({
                        'is_correct': is_correct,
                        'points_earned': points_earned,
                        'correct_answer': task.correct_answer,
                        'attempts': attempt_info.attempts if attempt_info else 1,
                        'next_task_id': next_task_id
                    })
        except Exception as e:
            logger.error(f"Error in task_view POST: {e}", exc_info=True)
            if is_ajax:
                return JsonResponse({'error': 'Произошла ошибка. Попробуйте позже.'}, status=500)
            messages.error(request, 'Произошла ошибка. Попробуйте позже.')
            return redirect(f'/task/{task_id}/')
    
    # Получаем все задачи этой темы для навигации и правильного счетчика X из N
    # Важно: счетчик и навигация должны считаться по полному списку задач темы,
    # а продолжение "с места" обеспечивается topic_view (редирект на первую нерешённую).
    if task.topic:
        topic_tasks = Task.objects.filter(topic=task.topic).order_by('order')
        task_list = list(topic_tasks)
        total_tasks = len(task_list)

        # Находим текущую позицию в ПОЛНОМ списке
        try:
            current_index = task_list.index(task)
            current_number = current_index + 1

            # Предыдущая и следующая задачи
            prev_task = task_list[current_index - 1] if current_index > 0 else None
            next_task = task_list[current_index + 1] if current_index < len(task_list) - 1 else None
        except ValueError:
            current_number = 1
            prev_task = None
            next_task = None
    else:
        total_tasks = 1
        current_number = 1
        prev_task = None
        next_task = None
    
    import json
    
    context = {
        'task': task,
        'result': result,
        'ai_reply': ai_reply,
        'total_tasks': total_tasks,
        'current_number': current_number,
        'prev_task': prev_task,
        'next_task': next_task,
        'points_earned': points_earned,
        'attempt_info': attempt_info,
        'task_options_json': json.dumps(task.options) if task.options else '{}',
    }
    return render(request, 'task.html', context)

def leaderboard_view(request):
    from .models import Leaderboard, UserProfile
    # Сортируем по очкам в порядке убывания
    leaderboard = Leaderboard.objects.select_related('user_profile__user').order_by('-points')
    
    # Получаем позицию и очки текущего пользователя
    user_rank = None
    user_points = 0
    total_users = leaderboard.count()
    
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            user_points = user_profile.xp
            
            # Находим позицию пользователя в рейтинге
            user_rank = Leaderboard.objects.filter(points__gt=user_points).count() + 1
        except UserProfile.DoesNotExist:
            pass
    
    context = {
        'leaderboard': leaderboard,
        'user_rank': user_rank,
        'user_points': user_points,
        'total_users': total_users,
    }
    return render(request, 'leaderboard.html', context)

def profile_view(request):
    from .models import UserProfile
    user_profile = None
    
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.select_related('user').get(user=request.user)
        except UserProfile.DoesNotExist:
            user_profile = None
        
        # Обработка изменения имени
        if request.method == 'POST' and 'first_name' in request.POST:
            first_name = request.POST.get('first_name', '').strip()
            if first_name:
                request.user.first_name = first_name
                request.user.save()
                messages.success(request, 'Имя успешно изменено!')
                return redirect('/profile/')
    
    return render(request, 'profile.html', {'user_profile': user_profile})

def login_view(request):
    from .forms import CustomLoginForm
    from .models import UserProfile
    import logging
    
    logger = logging.getLogger(__name__)
    error_message = None
    
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data.get('phone')
            password = form.cleaned_data.get('password')
            
            # Пробуем найти пользователя с номером (с + и без +)
            user_profile = None
            try:
                # Сначала пробуем точное совпадение
                user_profile = UserProfile.objects.get(phone=phone)
            except UserProfile.DoesNotExist:
                # Если не найдено, пробуем с + в начале
                try:
                    user_profile = UserProfile.objects.get(phone=f'+{phone}')
                except UserProfile.DoesNotExist:
                    # Если не найдено, пробуем без +
                    try:
                        user_profile = UserProfile.objects.get(phone=phone.lstrip('+'))
                    except UserProfile.DoesNotExist:
                        pass
            
            if user_profile:
                username = user_profile.user.username
                user = authenticate(username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    logger.info(f"User {user.username} (ID: {user.id}) logged in successfully from {request.META.get('REMOTE_ADDR')}")
                    return redirect('/')
                else:
                    error_message = 'Неверный пароль'
                    logger.warning(f"Failed login attempt for phone {phone} from {request.META.get('REMOTE_ADDR')}: wrong password")
            else:
                error_message = 'Пользователь с таким номером не найден'
                logger.warning(f"Failed login attempt for phone {phone} from {request.META.get('REMOTE_ADDR')}: user not found")
    else:
        form = CustomLoginForm()
    
    return render(request, 'login.html', {'form': form, 'error_message': error_message})

def register_view(request):
    from .forms import CustomUserCreationForm
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def demo_view(request):
    """Демо-страница для пробного тестирования без регистрации"""
    return render(request, 'demo.html')

def logout_view(request):
    logout(request)
    return redirect('/')

def password_reset_view(request):
    """Запрос на сброс пароля по номеру телефона"""
    from .models import UserProfile
    import secrets
    from django.core.cache import cache
    import re
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        phone_cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Если номер не начинается с +, добавляем +992
        if not phone_cleaned.startswith('+'):
            phone_cleaned = '+992' + phone_cleaned
        
        # Пробуем найти пользователя (с + и без +)
        user_profile = None
        try:
            user_profile = UserProfile.objects.get(phone=phone_cleaned)
        except UserProfile.DoesNotExist:
            try:
                user_profile = UserProfile.objects.get(phone=f'+{phone_cleaned}')
            except UserProfile.DoesNotExist:
                try:
                    user_profile = UserProfile.objects.get(phone=phone_cleaned.lstrip('+'))
                except UserProfile.DoesNotExist:
                    pass
        
        if user_profile:
            # Генерируем токен для сброса пароля
            reset_token = secrets.token_urlsafe(32)
            
            # Сохраняем токен в кэше на 1 час
            cache.set(f'password_reset_{reset_token}', user_profile.user.id, 3600)
            
            # В реальном приложении здесь отправляется SMS или email.
            # В DEBUG можно показать ссылку для удобства разработки.
            if settings.DEBUG:
                messages.success(request, f'Ссылка для сброса пароля: /password-reset-confirm/{reset_token}/')
        
        # Не раскрываем, существует ли пользователь (защита от перебора номеров)
        if not settings.DEBUG:
            messages.success(request, 'Если номер зарегистрирован, вы получите инструкции по сбросу пароля.')

    return render(request, 'password_reset.html')

def password_reset_confirm_view(request, token):
    """Установка нового пароля по токену"""
    from django.core.cache import cache
    from django.contrib.auth.models import User
    
    # Проверяем токен
    user_id = cache.get(f'password_reset_{token}')
    
    if not user_id:
        messages.error(request, 'Ссылка для сброса пароля недействительна или истекла')
        return redirect('/login/')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
        elif len(password1) < 8:
            messages.error(request, 'Пароль должен содержать минимум 8 символов')
        else:
            try:
                user = User.objects.get(id=user_id)
                user.set_password(password1)
                user.save()
                
                # Удаляем использованный токен
                cache.delete(f'password_reset_{token}')
                
                messages.success(request, 'Пароль успешно изменен! Теперь вы можете войти с новым паролем.')
                return redirect('/login/')
            except User.DoesNotExist:
                messages.error(request, 'Ошибка при сбросе пароля')
    
    return render(request, 'password_reset_confirm.html')

def admin_password_reset_view(request):
    """Административная страница сброса пароля"""
    from django.contrib.auth.decorators import login_required
    from django.contrib.auth.decorators import user_passes_test
    from .models import UserProfile
    
    # Проверяем, является ли пользователь суперпользователем или персоналом
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'Доступ запрещен. Требуются права администратора.')
        return redirect('/login/')
    
    # Получаем всех пользователей с профилями
    users = User.objects.select_related('userprofile').all()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if not user_id:
            messages.error(request, 'Выберите пользователя')
        elif password1 != password2:
            messages.error(request, 'Пароли не совпадают')
        elif len(password1) < 8:
            messages.error(request, 'Пароль должен содержать минимум 8 символов')
        else:
            try:
                user = User.objects.get(id=user_id)
                user.set_password(password1)
                user.save()
                
                messages.success(request, f'Пароль успешно изменен для пользователя: {user.first_name} {user.last_name}')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь не найден')
    
    return render(request, 'admin_password_reset.html', {'users': users})

@api_view(['POST'])
def gmini_api(request):
    """
    Пример AI ассистента: принимает {"message": "..."}, возвращает ответ.
    """
    user_message = request.data.get('message', '')
    # Здесь будет интеграция с AI, пока просто echo
    return Response({'reply': f'AI (echo): {user_message}'})

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class LeaderboardViewSet(viewsets.ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer


def sitemap_view(request):
    """Генерация XML sitemap для поисковых систем"""
    from django.http import HttpResponse
    from django.urls import reverse
    from datetime import datetime
    
    subjects = Subject.objects.all()
    
    sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://hushyor.com/</loc>
        <lastmod>{}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://hushyor.com/leaderboard/</loc>
        <lastmod>{}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://hushyor.com/login/</loc>
        <lastmod>{}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>
    <url>
        <loc>https://hushyor.com/register/</loc>
        <lastmod>{}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>'''.format(
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%Y-%m-%d')
    )
    
    # Добавляем страницы предметов
    for subject in subjects:
        sitemap_xml += '''
    <url>
        <loc>https://hushyor.com/subject/{}/</loc>
        <lastmod>{}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>'''.format(subject.id, datetime.now().strftime('%Y-%m-%d'))
    
    sitemap_xml += '\n</urlset>'
    
    return HttpResponse(sitemap_xml, content_type='application/xml')


def robots_txt_view(request):
    """Генерация robots.txt"""
    from django.http import HttpResponse
    
    robots_txt = """User-agent: *
Allow: /
Allow: /subject/
Allow: /leaderboard/
Disallow: /admin/
Disallow: /hushyor-control-panel/
Disallow: /api/
Disallow: /profile/
Disallow: /logout/

Sitemap: https://hushyor.com/sitemap.xml

Crawl-delay: 1
"""
    
    return HttpResponse(robots_txt, content_type='text/plain')


def yandex_verification_view(request):
    """Верификация для Yandex Webmaster"""
    from django.shortcuts import render
    return render(request, 'yandex_f58006ecd2f5e538.html')


def task_og_image_view(request, task_id):
    """Генерирует Open Graph изображение для задачи с поддержкой таджикского языка"""
    from django.http import HttpResponse, Http404
    from .models import Task
    from .og_image_generator import generate_task_og_image
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        task = Task.objects.select_related('subject').get(id=task_id)
    except Task.DoesNotExist:
        logger.warning(f"Task {task_id} not found for OG image generation")
        raise Http404("Task not found")
    
    try:
        # Генерируем изображение
        image_buffer = generate_task_og_image(task)
        
        # Возвращаем PNG с правильными заголовками для кэширования
        response = HttpResponse(image_buffer.getvalue(), content_type='image/png')
        # Важно: no-cache для соцсетей, чтобы они не кэшировали пустые изображения
        # После исправления можно изменить на: 'public, max-age=86400'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        # Добавляем заголовки для отладки
        response['X-Content-Type-Options'] = 'nosniff'
        return response
        
    except Exception as e:
        logger.error(f"Error generating OG image for task {task_id}: {str(e)}", exc_info=True)
        # Возвращаем простое изображение-заглушку в случае ошибки
        from PIL import Image, ImageDraw, ImageFont
        from io import BytesIO
        import os
        
        # Создаем простую заглушку
        img = Image.new('RGB', (1200, 630), color='#4F6DF5')
        draw = ImageDraw.Draw(img)
        
        # Пытаемся загрузить шрифт для заглушки
        try:
            font_path = os.path.join(settings.BASE_DIR, 'core', 'fonts', 'DejaVuSans-Bold.ttf')
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, 48)
                draw.text((60, 280), "hushyor.com", fill='white', font=font)
                draw.text((60, 340), "Ошибка загрузки изображения", fill='white', font=ImageFont.truetype(font_path, 32))
            else:
                draw.text((60, 300), "hushyor.com", fill='white')
        except Exception as font_error:
            logger.error(f"Error loading font for fallback image: {str(font_error)}")
            # Последний fallback без шрифтов
            pass
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
