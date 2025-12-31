from django.core.management.base import BaseCommand
from core.models import Subject, Task, UserProfile, Leaderboard
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Создать тестовые данные для проекта'

    def handle(self, *args, **kwargs):
        # Создать тестового пользователя
        if not User.objects.filter(username='testuser').exists():
            user = User.objects.create_user(username='testuser', password='testpass123')
            UserProfile.objects.create(user=user, phone='+7 999 123 45 67', streak=7, xp=1250)
            Leaderboard.objects.create(user_profile=user.userprofile, points=1250)
            self.stdout.write(self.style.SUCCESS('Создан тестовый пользователь: testuser / testpass123'))

        # Создать предметы
        subjects_data = [
            {'title': 'Математика', 'icon': '📐', 'color': '#3b82f6'},
            {'title': 'Русский язык', 'icon': '📚', 'color': '#ef4444'},
            {'title': 'Физика', 'icon': '⚛️', 'color': '#10b981'},
        ]
        
        for data in subjects_data:
            subject, created = Subject.objects.get_or_create(title=data['title'], defaults=data)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан предмет: {subject.title}'))

        # Создать задания
        math = Subject.objects.get(title='Математика')
        russian = Subject.objects.get(title='Русский язык')
        physics = Subject.objects.get(title='Физика')

        tasks_data = [
            {
                'subject': math,
                'question': 'Решите уравнение: 2x + 5 = 13',
                'options': ['x = 3', 'x = 4', 'x = 5', 'x = 6'],
                'correct_answer': 'x = 4',
                'difficulty': 2
            },
            {
                'subject': math,
                'question': 'Найдите производную функции f(x) = x²',
                'options': ['f\'(x) = x', 'f\'(x) = 2x', 'f\'(x) = x²', 'f\'(x) = 2'],
                'correct_answer': 'f\'(x) = 2x',
                'difficulty': 3
            },
            {
                'subject': russian,
                'question': 'Выберите правильное написание слова:',
                'options': ['прийти', 'придти', 'прити', 'притти'],
                'correct_answer': 'прийти',
                'difficulty': 2
            },
            {
                'subject': physics,
                'question': 'Формула второго закона Ньютона:',
                'options': ['F = ma', 'E = mc²', 'P = mv', 'W = Fs'],
                'correct_answer': 'F = ma',
                'difficulty': 2
            },
        ]

        for data in tasks_data:
            task, created = Task.objects.get_or_create(
                subject=data['subject'],
                question=data['question'],
                defaults={
                    'options': data['options'],
                    'correct_answer': data['correct_answer'],
                    'difficulty': data['difficulty']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создано задание: {task.question[:50]}...'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
