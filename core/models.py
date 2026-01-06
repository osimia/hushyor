from django.db import models

from django.contrib.auth.models import User

class Subject(models.Model):
    title = models.CharField(max_length=255)
    icon = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.title

class Topic(models.Model):
    subject = models.ForeignKey(Subject, related_name='topics', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.subject.title} - {self.title}"

class Task(models.Model):
    subject = models.ForeignKey(Subject, related_name='tasks', on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, related_name='tasks', on_delete=models.CASCADE, null=True, blank=True)
    question = models.TextField()
    options = models.JSONField(blank=True, null=True)
    correct_answer = models.CharField(max_length=255, blank=True)
    difficulty = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    original_test_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.subject.title}: {self.question[:30]}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=32, blank=True)
    streak = models.IntegerField(default=0)
    xp = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

class Leaderboard(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-points']

    def __str__(self):
        return f"{self.user_profile.user.username}: {self.points}"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    completed_tasks = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'subject')
        verbose_name_plural = 'User Progress'
    
    def __str__(self):
        return f"{self.user.username} - {self.subject.title}"
    
    @property
    def progress_percentage(self):
        if self.total_tasks == 0:
            return 0
        return int((self.completed_tasks / self.total_tasks) * 100)

class TaskAttempt(models.Model):
    """Отслеживание попыток решения задач"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    attempts = models.IntegerField(default=0)
    is_solved = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'task')
        verbose_name_plural = 'Task Attempts'
    
    def __str__(self):
        return f"{self.user.username} - {self.task.question[:30]} - {self.attempts} попыток"
