from django.core.management.base import BaseCommand
from django.core import serializers
from core.models import Subject, Topic, Task, UserProfile, Leaderboard
import json


class Command(BaseCommand):
    help = 'Экспортирует все данные в JSON файл'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='export_data.json',
            help='Имя выходного файла'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        
        self.stdout.write(self.style.SUCCESS('📦 Экспорт данных...'))
        
        # Собираем все объекты
        all_objects = []
        
        # Предметы
        subjects = list(Subject.objects.all())
        all_objects.extend(subjects)
        self.stdout.write(f'  ✓ Предметов: {len(subjects)}')
        
        # Темы
        topics = list(Topic.objects.all())
        all_objects.extend(topics)
        self.stdout.write(f'  ✓ Тем: {len(topics)}')
        
        # Задания
        tasks = list(Task.objects.all())
        all_objects.extend(tasks)
        self.stdout.write(f'  ✓ Заданий: {len(tasks)}')
        
        # Профили пользователей (опционально)
        try:
            profiles = list(UserProfile.objects.all())
            all_objects.extend(profiles)
            self.stdout.write(f'  ✓ Профилей: {len(profiles)}')
        except:
            pass
        
        # Сериализуем в JSON
        data = serializers.serialize('json', all_objects, indent=2)
        
        # Сохраняем в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(data)
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Данные экспортированы в {output_file}'))
        self.stdout.write(f'📊 Всего объектов: {len(all_objects)}')
        self.stdout.write('\nДля импорта на продакшене:')
        self.stdout.write(self.style.WARNING(f'python manage.py loaddata {output_file}'))
