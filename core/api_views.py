"""
API Views для мобильного приложения Flutter
Все эндпоинты возвращают JSON и работают параллельно с существующими HTML-шаблонами
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Count, Q

from .models import Subject, Topic, Task, UserProfile, TaskAttempt, Leaderboard
from .serializers import (
    SubjectSerializer, SubjectDetailSerializer,
    TopicSerializer, TopicDetailSerializer,
    TaskSerializer, TaskDetailSerializer,
    UserSerializer, UserProfileSerializer,
    UserRegistrationSerializer, SubmitAnswerSerializer,
    LeaderboardSerializer
)


# ==================== Аутентификация ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """
    Регистрация нового пользователя
    POST /api/auth/register/
    Body: {username, password, password2, phone, full_name, email}
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Регистрация успешна',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Вход пользователя
    POST /api/auth/login/
    Body: {username, password} или {phone, password}
    """
    username = request.data.get('username')
    phone = request.data.get('phone')
    password = request.data.get('password')
    
    user = None
    
    # Попытка входа по телефону
    if phone and not username:
        try:
            profile = UserProfile.objects.get(phone=phone)
            user = authenticate(username=profile.user.username, password=password)
        except UserProfile.DoesNotExist:
            pass
    
    # Попытка входа по username
    if username and not user:
        user = authenticate(username=username, password=password)
    
    if user:
        refresh = RefreshToken.for_user(user)
        profile = UserProfile.objects.get(user=user)
        
        return Response({
            'success': True,
            'message': 'Вход выполнен успешно',
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    
    return Response({
        'success': False,
        'message': 'Неверные учетные данные'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """
    Получить профиль текущего пользователя
    GET /api/auth/profile/
    """
    profile = UserProfile.objects.get(user=request.user)
    return Response({
        'user': UserSerializer(request.user).data,
        'profile': UserProfileSerializer(profile).data
    })


# ==================== Главная страница ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def home_api(request):
    """
    Главная страница - список всех предметов с прогрессом
    GET /api/home/
    """
    subjects = Subject.objects.annotate(total_tasks_count=Count('tasks'))
    
    # Статистика
    stats = {
        'total_users': User.objects.count(),
        'total_tasks': Task.objects.count(),
        'total_subjects': Subject.objects.count(),
    }
    
    # Если пользователь авторизован, добавляем прогресс
    if request.user.is_authenticated:
        serializer = SubjectDetailSerializer(subjects, many=True, context={'request': request})
    else:
        serializer = SubjectSerializer(subjects, many=True)
    
    return Response({
        'subjects': serializer.data,
        'stats': stats
    })


# ==================== Предметы ====================

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для предметов
    GET /api/subjects/ - список всех предметов
    GET /api/subjects/{id}/ - детальная информация о предмете с темами
    """
    queryset = Subject.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubjectDetailSerializer
        return SubjectSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}


# ==================== Темы ====================

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для тем
    GET /api/topics/ - список всех тем
    GET /api/topics/{id}/ - детальная информация о теме
    GET /api/topics/{id}/tasks/ - список задач в теме
    """
    queryset = Topic.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TopicDetailSerializer
        return TopicSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Получить все задачи для конкретной темы"""
        topic = self.get_object()
        tasks = Task.objects.filter(topic=topic).order_by('order')
        
        if request.user.is_authenticated:
            serializer = TaskDetailSerializer(tasks, many=True, context={'request': request})
        else:
            serializer = TaskSerializer(tasks, many=True)
        
        return Response({
            'topic': TopicDetailSerializer(topic, context={'request': request}).data,
            'tasks': serializer.data
        })


# ==================== Задачи ====================

class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для задач
    GET /api/tasks/ - список всех задач
    GET /api/tasks/{id}/ - детальная информация о задаче
    POST /api/tasks/{id}/submit/ - отправить ответ на задачу
    """
    queryset = Task.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """
        Отправить ответ на задачу
        POST /api/tasks/{id}/submit/
        Body: {answer: "1" | "2" | "3" | "4"}
        """
        task = self.get_object()
        answer = request.data.get('answer')
        
        if not answer:
            return Response({
                'success': False,
                'message': 'Ответ не указан'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Получаем или создаем попытку
        attempt, created = TaskAttempt.objects.get_or_create(
            user=request.user,
            task=task
        )
        
        # Увеличиваем счетчик попыток
        attempt.attempts += 1
        
        # Проверяем правильность ответа
        is_correct = str(answer) == str(task.correct_answer)
        
        if is_correct and not attempt.is_solved:
            attempt.is_solved = True
            # Начисляем очки (можно настроить логику)
            points = max(10 - attempt.attempts, 1)  # Чем меньше попыток, тем больше очков
            attempt.points_earned = points
            
            # Обновляем профиль пользователя
            profile = UserProfile.objects.get(user=request.user)
            profile.xp += points
            profile.save()
            
            # Обновляем leaderboard
            leaderboard, _ = Leaderboard.objects.get_or_create(user_profile=profile)
            leaderboard.points = profile.xp
            leaderboard.save()
        
        attempt.save()
        
        return Response({
            'success': True,
            'is_correct': is_correct,
            'is_solved': attempt.is_solved,
            'attempts': attempt.attempts,
            'points_earned': attempt.points_earned if is_correct else 0,
            'correct_answer': task.correct_answer if is_correct or attempt.attempts >= 3 else None,
            'message': 'Правильно! 🎉' if is_correct else 'Неправильно, попробуйте еще раз'
        })


# ==================== Прогресс пользователя ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_progress_api(request):
    """
    Получить прогресс пользователя по всем предметам
    GET /api/progress/
    """
    subjects = Subject.objects.all()
    progress_data = []
    
    for subject in subjects:
        total_tasks = subject.tasks.count()
        completed_tasks = TaskAttempt.objects.filter(
            user=request.user,
            task__subject=subject,
            is_solved=True
        ).count()
        
        progress_data.append({
            'subject_id': subject.id,
            'subject_title': subject.title,
            'subject_icon': subject.icon,
            'subject_color': subject.color,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percentage': int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        })
    
    return Response({
        'progress': progress_data,
        'total_xp': request.user.userprofile.xp,
        'streak': request.user.userprofile.streak
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def topic_progress_api(request, topic_id):
    """
    Получить прогресс пользователя по конкретной теме
    GET /api/progress/topic/{topic_id}/
    """
    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Тема не найдена'
        }, status=status.HTTP_404_NOT_FOUND)
    
    tasks = Task.objects.filter(topic=topic).order_by('order')
    tasks_data = []
    
    for task in tasks:
        attempt = TaskAttempt.objects.filter(user=request.user, task=task).first()
        tasks_data.append({
            'task_id': task.id,
            'question': task.question,
            'order': task.order,
            'is_solved': attempt.is_solved if attempt else False,
            'attempts': attempt.attempts if attempt else 0
        })
    
    completed_count = sum(1 for t in tasks_data if t['is_solved'])
    
    return Response({
        'topic': TopicDetailSerializer(topic, context={'request': request}).data,
        'tasks': tasks_data,
        'total_tasks': len(tasks_data),
        'completed_tasks': completed_count,
        'progress_percentage': int((completed_count / len(tasks_data)) * 100) if tasks_data else 0
    })


# ==================== Leaderboard ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard_api(request):
    """
    Получить таблицу лидеров
    GET /api/leaderboard/
    """
    leaderboard = Leaderboard.objects.select_related('user_profile__user').order_by('-points')[:100]
    serializer = LeaderboardSerializer(leaderboard, many=True)
    
    # Если пользователь авторизован, добавляем его позицию
    user_rank = None
    if request.user.is_authenticated:
        try:
            user_entry = Leaderboard.objects.get(user_profile__user=request.user)
            user_rank = Leaderboard.objects.filter(points__gt=user_entry.points).count() + 1
        except Leaderboard.DoesNotExist:
            user_rank = None
    
    return Response({
        'leaderboard': serializer.data,
        'user_rank': user_rank
    })


# ==================== Статистика ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats_api(request):
    """
    Получить детальную статистику пользователя
    GET /api/stats/
    """
    profile = UserProfile.objects.get(user=request.user)
    
    total_solved = TaskAttempt.objects.filter(user=request.user, is_solved=True).count()
    total_attempts = TaskAttempt.objects.filter(user=request.user).aggregate(
        total=Count('id')
    )['total'] or 0
    
    # Статистика по предметам
    subjects_stats = []
    for subject in Subject.objects.all():
        subject_tasks = subject.tasks.count()
        subject_solved = TaskAttempt.objects.filter(
            user=request.user,
            task__subject=subject,
            is_solved=True
        ).count()
        
        if subject_tasks > 0:
            subjects_stats.append({
                'subject_id': subject.id,
                'subject_title': subject.title,
                'subject_icon': subject.icon,
                'total_tasks': subject_tasks,
                'solved_tasks': subject_solved,
                'progress_percentage': int((subject_solved / subject_tasks) * 100)
            })
    
    return Response({
        'profile': UserProfileSerializer(profile).data,
        'total_solved': total_solved,
        'total_attempts': total_attempts,
        'subjects_stats': subjects_stats,
        'leaderboard_rank': Leaderboard.objects.filter(
            points__gt=profile.xp
        ).count() + 1 if Leaderboard.objects.filter(user_profile=profile).exists() else None
    })
