from django.shortcuts import render, redirect
from .models import Subject
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

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
    from .models import UserProgress, Task
    from django.db.models import Count
    
    subjects = Subject.objects.all()
    
    # Получаем прогресс для текущего пользователя
    user_progress = {}
    if request.user.is_authenticated:
        progress_data = UserProgress.objects.filter(user=request.user).select_related('subject')
        user_progress = {p.subject.id: p for p in progress_data}
    
    # Добавляем информацию о прогрессе к каждому предмету
    subjects_with_progress = []
    for subject in subjects:
        progress = user_progress.get(subject.id)
        subject.user_progress = progress
        subject.completed = progress.completed_tasks if progress else 0
        subject.total = progress.total_tasks if progress else subject.tasks.count()
        subject.percentage = progress.progress_percentage if progress else 0
        subjects_with_progress.append(subject)
    
    # Статистика для главной страницы
    stats = {
        'total_users': User.objects.count(),
        'total_tasks': Task.objects.count(),
        'total_subjects': Subject.objects.count(),
    }
    
    return render(request, 'main.html', {
        'subjects': subjects_with_progress,
        'stats': stats
    })

def subject_view(request, subject_id):
    from .models import Task, Topic, UserProgress, TaskAttempt
    subject = Subject.objects.get(id=subject_id)
    topics = Topic.objects.filter(subject=subject).prefetch_related('tasks')
    
    # Calculate progress for each topic
    total_completed = 0
    for topic in topics:
        topic.total_count = topic.tasks.count()
        topic.completed_count = 0
        
        # Подсчет решенных задач для авторизованного пользователя
        if request.user.is_authenticated:
            topic_task_ids = topic.tasks.values_list('id', flat=True)
            topic.completed_count = TaskAttempt.objects.filter(
                user=request.user,
                task_id__in=topic_task_ids,
                is_solved=True
            ).count()
            total_completed += topic.completed_count
        
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
    from .models import Task, Topic
    topic = Topic.objects.get(id=topic_id)
    tasks = Task.objects.filter(topic=topic).order_by('order')
    
    # Redirect to first task if tasks exist
    if tasks.exists():
        first_task = tasks.first()
        return redirect(f'/task/{first_task.id}/')
    else:
        # No tasks, redirect back to subject
        return redirect(f'/subject/{topic.subject.id}/')

def task_view(request, task_id):
    from .models import Task, TaskAttempt, UserProfile, Leaderboard
    from .ai_helper import get_theory_lesson, get_hint, get_ai_response
    from django.http import JsonResponse
    
    task = Task.objects.get(id=task_id)
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
    
    if request.method == 'POST':
        # Проверяем, это AJAX запрос или нет
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if 'theory' in request.POST:
            # Запрос теории
            ai_reply = get_theory_lesson(task.question, task.subject.title)
            if is_ajax:
                return JsonResponse({'ai_reply': ai_reply})
        elif 'hint' in request.POST:
            # Запрос подсказки
            ai_reply = get_hint(task.question, task.subject.title)
            if is_ajax:
                return JsonResponse({'ai_reply': ai_reply})
        elif 'ai_message' in request.POST:
            # Произвольный вопрос к ИИ
            message = request.POST.get('ai_message', '')
            if message.strip():
                ai_reply = get_ai_response(message, task.question, task.subject.title)
                if is_ajax:
                    return JsonResponse({'ai_reply': ai_reply})
        else:
            # Проверка ответа
            answer = request.POST.get('answer', '').strip()
            is_correct = (answer == task.correct_answer)
            result = is_correct
            
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
                            profile = UserProfile.objects.get(user=request.user)
                            profile.xp += points_earned
                            profile.save()
                            
                            # Обновляем таблицу лидеров
                            leaderboard, _ = Leaderboard.objects.get_or_create(user_profile=profile)
                            leaderboard.points = profile.xp
                            leaderboard.save()
                        except UserProfile.DoesNotExist:
                            pass
                    
                    attempt_info.save()
    
    # Получаем все задачи этой темы для навигации
    if task.topic:
        topic_tasks = Task.objects.filter(topic=task.topic).order_by('order')
        total_tasks = topic_tasks.count()
        
        # Находим текущую позицию
        task_list = list(topic_tasks)
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
    }
    return render(request, 'task.html', context)

def leaderboard_view(request):
    from .models import Leaderboard, UserProfile
    leaderboard = Leaderboard.objects.select_related('user_profile__user').all()
    
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
    return render(request, 'profile.html', {'user_profile': user_profile})

def login_view(request):
    from .forms import CustomLoginForm
    from .models import UserProfile
    
    error_message = None
    
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data.get('phone')
            password = form.cleaned_data.get('password')
            
            # Находим username по номеру телефона
            try:
                user_profile = UserProfile.objects.get(phone=phone)
                username = user_profile.user.username
                user = authenticate(username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    return redirect('/')
                else:
                    error_message = 'Неверный пароль'
            except UserProfile.DoesNotExist:
                error_message = 'Пользователь с таким номером не найден'
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

def logout_view(request):
    logout(request)
    return redirect('/')

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
