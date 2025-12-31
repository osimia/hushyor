from rest_framework import serializers
from .models import Subject, Task, UserProfile, Leaderboard, UserProgress
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
