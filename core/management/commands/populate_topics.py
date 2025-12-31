from django.core.management.base import BaseCommand
from core.models import Subject, Topic, Task

class Command(BaseCommand):
    help = 'Populate database with topics and tasks for subjects'

    def handle(self, *args, **kwargs):
        # Получаем предмет Математика
        try:
            math = Subject.objects.get(title='Математика')
        except Subject.DoesNotExist:
            self.stdout.write(self.style.ERROR('Предмет "Математика" не найден. Сначала запустите populate_subjects'))
            return

        # Создаем темы для математики
        topics_data = [
            {'title': 'Уравнения', 'order': 1, 'is_locked': False},
            {'title': 'Неравенства', 'order': 2, 'is_locked': False},
            {'title': 'Геометрия', 'order': 3, 'is_locked': True},
        ]

        for topic_data in topics_data:
            topic, created = Topic.objects.get_or_create(
                subject=math,
                title=topic_data['title'],
                defaults={
                    'order': topic_data['order'],
                    'is_locked': topic_data['is_locked'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Создана тема: {topic.title}'))
                
                # Добавляем задачи для темы "Уравнения"
                if topic.title == 'Уравнения':
                    tasks = [
                        {
                            'question': 'Решите уравнение: 2x + 5 = 15',
                            'options': ['3', '5', '7', '10'],
                            'correct_answer': '5',
                            'difficulty': 1,
                            'order': 1,
                        },
                        {
                            'question': 'Решите уравнение: 3x - 7 = 14',
                            'options': ['5', '7', '9', '11'],
                            'correct_answer': '7',
                            'difficulty': 1,
                            'order': 2,
                        },
                        {
                            'question': 'Решите уравнение: x² - 4 = 0',
                            'options': ['±1', '±2', '±3', '±4'],
                            'correct_answer': '±2',
                            'difficulty': 2,
                            'order': 3,
                        },
                        {
                            'question': 'Решите уравнение: 2x² + 5x - 3 = 0',
                            'options': ['x₁=-3, x₂=0.5', 'x₁=-2, x₂=1', 'x₁=-1, x₂=3', 'x₁=0, x₂=2'],
                            'correct_answer': 'x₁=-3, x₂=0.5',
                            'difficulty': 3,
                            'order': 4,
                        },
                    ]
                    
                    for task_data in tasks:
                        Task.objects.get_or_create(
                            subject=math,
                            topic=topic,
                            question=task_data['question'],
                            defaults={
                                'options': task_data['options'],
                                'correct_answer': task_data['correct_answer'],
                                'difficulty': task_data['difficulty'],
                                'order': task_data['order'],
                            }
                        )
                    self.stdout.write(self.style.SUCCESS(f'  → Добавлено {len(tasks)} задач'))
                
                # Добавляем задачи для темы "Неравенства"
                elif topic.title == 'Неравенства':
                    tasks = [
                        {
                            'question': 'Решите неравенство: 2x + 3 > 7',
                            'options': ['x > 2', 'x > 3', 'x > 4', 'x > 5'],
                            'correct_answer': 'x > 2',
                            'difficulty': 1,
                            'order': 1,
                        },
                        {
                            'question': 'Решите неравенство: 5x - 10 ≤ 15',
                            'options': ['x ≤ 3', 'x ≤ 4', 'x ≤ 5', 'x ≤ 6'],
                            'correct_answer': 'x ≤ 5',
                            'difficulty': 2,
                            'order': 2,
                        },
                    ]
                    
                    for task_data in tasks:
                        Task.objects.get_or_create(
                            subject=math,
                            topic=topic,
                            question=task_data['question'],
                            defaults={
                                'options': task_data['options'],
                                'correct_answer': task_data['correct_answer'],
                                'difficulty': task_data['difficulty'],
                                'order': task_data['order'],
                            }
                        )
                    self.stdout.write(self.style.SUCCESS(f'  → Добавлено {len(tasks)} задач'))
            else:
                self.stdout.write(self.style.WARNING(f'→ Тема уже существует: {topic.title}'))

        self.stdout.write(self.style.SUCCESS('\n✓ Загрузка тем и задач завершена!'))
