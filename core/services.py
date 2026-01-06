"""
Сервисный слой для работы с задачами
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from core.models import Task, TaskAttempt, UserProfile, Leaderboard
import logging

logger = logging.getLogger(__name__)


class TaskService:
    """Сервис для работы с задачами и ответами"""
    
    @staticmethod
    @transaction.atomic
    def submit_answer(user, task, answer):
        """
        Обработка ответа пользователя на задачу
        
        Args:
            user: User объект
            task: Task объект
            answer: Ответ пользователя (строка)
            
        Returns:
            tuple: (attempt, is_correct, points_earned)
            
        Raises:
            ValidationError: Если ответ невалиден
        """
        # Валидация
        if not answer or len(answer) > 100:
            raise ValidationError("Ответ должен быть от 1 до 100 символов")
        
        # Получаем или создаем попытку
        attempt, created = TaskAttempt.objects.select_for_update().get_or_create(
            user=user,
            task=task
        )
        
        attempt.attempts += 1
        is_correct = str(answer).strip() == str(task.correct_answer).strip()
        points_earned = 0
        
        if is_correct and not attempt.is_solved:
            # Рассчитываем и начисляем очки
            points_earned = TaskService._calculate_points(task, attempt)
            TaskService._award_points(user, points_earned)
            
            attempt.is_solved = True
            attempt.points_earned = points_earned
            
            logger.info(f"User {user.id} solved task {task.id}, earned {points_earned} points")
        
        attempt.save()
        
        return attempt, is_correct, points_earned
    
    @staticmethod
    def _calculate_points(task, attempt):
        """
        Расчет очков за решение задачи
        
        Args:
            task: Task объект
            attempt: TaskAttempt объект
            
        Returns:
            int: Количество очков
        """
        base_points = task.difficulty * 5
        
        if attempt.attempts == 1:
            return base_points  # 100% за первую попытку
        elif attempt.attempts == 2:
            return int(base_points * 0.7)  # 70% за вторую
        else:
            return int(base_points * 0.5)  # 50% за остальные
    
    @staticmethod
    def _award_points(user, points):
        """
        Начисление очков пользователю
        
        Args:
            user: User объект
            points: Количество очков
        """
        profile, created = UserProfile.objects.select_for_update().get_or_create(user=user)
        profile.xp += points
        profile.save()
        
        # Обновляем leaderboard
        leaderboard, _ = Leaderboard.objects.get_or_create(user_profile=profile)
        leaderboard.points = profile.xp
        leaderboard.save()
    
    @staticmethod
    def get_user_progress(user, subject=None):
        """
        Получение прогресса пользователя
        
        Args:
            user: User объект
            subject: Subject объект (опционально)
            
        Returns:
            dict: Статистика прогресса
        """
        from django.db.models import Count, Q
        
        query = TaskAttempt.objects.filter(user=user)
        if subject:
            query = query.filter(task__subject=subject)
        
        stats = query.aggregate(
            total_attempts=Count('id'),
            solved=Count('id', filter=Q(is_solved=True))
        )
        
        return {
            'total_attempts': stats['total_attempts'] or 0,
            'solved': stats['solved'] or 0,
            'percentage': int((stats['solved'] / stats['total_attempts'] * 100)) if stats['total_attempts'] else 0
        }
