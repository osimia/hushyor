from rest_framework import serializers
from .models import Subject, Task, UserProfile, Leaderboard, UserProgress, Topic, TaskAttempt
from django.contrib.auth.models import User

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = UserProfile
        fields = '__all__'

class LeaderboardSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)
    class Meta:
        model = Leaderboard
        fields = '__all__'

class UserProgressSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProgress
        fields = '__all__'


class TopicSerializer(serializers.ModelSerializer):
    """Базовый serializer для темы"""
    class Meta:
        model = Topic
        fields = ['id', 'title', 'order', 'is_locked', 'subject']


class TopicDetailSerializer(serializers.ModelSerializer):
    """Детальный serializer темы с количеством задач и прогрессом"""
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = ['id', 'title', 'order', 'is_locked', 'subject', 'total_tasks', 'completed_tasks', 'progress_percentage']
    
    def get_total_tasks(self, obj):
        return obj.tasks.count()
    
    def get_completed_tasks(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            task_ids = obj.tasks.values_list('id', flat=True)
            return TaskAttempt.objects.filter(
                user=request.user,
                task_id__in=task_ids,
                is_solved=True
            ).count()
        return 0
    
    def get_progress_percentage(self, obj):
        total = self.get_total_tasks(obj)
        completed = self.get_completed_tasks(obj)
        return int((completed / total) * 100) if total > 0 else 0


class SubjectDetailSerializer(serializers.ModelSerializer):
    """Детальный serializer предмета с прогрессом пользователя"""
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    topics = TopicDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Subject
        fields = ['id', 'title', 'icon', 'color', 'total_tasks', 'completed_tasks', 'progress_percentage', 'topics']
    
    def get_total_tasks(self, obj):
        return obj.tasks.count()
    
    def get_completed_tasks(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return TaskAttempt.objects.filter(
                user=request.user,
                task__subject=obj,
                is_solved=True
            ).count()
        return 0
    
    def get_progress_percentage(self, obj):
        total = self.get_total_tasks(obj)
        completed = self.get_completed_tasks(obj)
        return int((completed / total) * 100) if total > 0 else 0


class TaskAttemptSerializer(serializers.ModelSerializer):
    """Serializer для попыток решения задач"""
    class Meta:
        model = TaskAttempt
        fields = ['id', 'task', 'attempts', 'is_solved', 'points_earned', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class TaskDetailSerializer(serializers.ModelSerializer):
    """Детальный serializer задачи с информацией о попытках пользователя"""
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    is_solved = serializers.SerializerMethodField()
    attempts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = ['id', 'subject', 'subject_title', 'topic', 'topic_title', 'question', 
                  'options', 'correct_answer', 'difficulty', 'order', 'is_solved', 'attempts_count']
    
    def get_is_solved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempt = TaskAttempt.objects.filter(user=request.user, task=obj).first()
            return attempt.is_solved if attempt else False
        return False
    
    def get_attempts_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            attempt = TaskAttempt.objects.filter(user=request.user, task=obj).first()
            return attempt.attempts if attempt else 0
        return 0


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer для регистрации нового пользователя"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    phone = serializers.CharField(required=True)
    full_name = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'phone', 'full_name', 'email']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        phone = validated_data.pop('phone')
        full_name = validated_data.pop('full_name', '')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        
        if full_name:
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
            user.save()
        
        UserProfile.objects.create(user=user, phone=phone)
        return user


class SubmitAnswerSerializer(serializers.Serializer):
    """Serializer для отправки ответа на задачу"""
    task_id = serializers.IntegerField()
    answer = serializers.CharField()
    
    def validate_task_id(self, value):
        if not Task.objects.filter(id=value).exists():
            raise serializers.ValidationError("Задача не найдена")
        return value
