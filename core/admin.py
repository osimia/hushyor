from django.contrib import admin
from .models import Subject, Topic, Task, UserProfile, Leaderboard, UserProgress, TaskAttempt

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'color', 'task_count')
    search_fields = ('title',)
    list_filter = ('title',)
    
    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Количество задач'

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'order', 'is_locked', 'task_count')
    list_filter = ('subject', 'is_locked')
    search_fields = ('title',)
    ordering = ('subject', 'order')
    
    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Количество задач'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('subject', 'topic', 'question_preview', 'difficulty', 'order', 'correct_answer')
    list_filter = ('subject', 'topic', 'difficulty')
    search_fields = ('question', 'correct_answer')
    ordering = ('subject', 'topic', 'order')
    
    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Вопрос'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'streak', 'xp')
    search_fields = ('user__username', 'phone')
    list_filter = ('streak',)

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'points', 'updated')
    list_filter = ('updated',)
    search_fields = ('user_profile__user__username',)
    ordering = ('-points',)

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'completed_tasks', 'total_tasks', 'progress_percentage')
    list_filter = ('subject', 'user')
    search_fields = ('user__username', 'subject__title')
    
    def progress_percentage(self, obj):
        return f"{obj.progress_percentage}%"
    progress_percentage.short_description = 'Прогресс'

@admin.register(TaskAttempt)
class TaskAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'task_preview', 'attempts', 'is_solved', 'points_earned', 'updated_at')
    list_filter = ('is_solved', 'attempts', 'updated_at')
    search_fields = ('user__username', 'task__question')
    ordering = ('-updated_at',)
    
    def task_preview(self, obj):
        return obj.task.question[:50] + '...' if len(obj.task.question) > 50 else obj.task.question
    task_preview.short_description = 'Задача'
