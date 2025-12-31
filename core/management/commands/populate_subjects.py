from django.core.management.base import BaseCommand
from core.models import Subject

class Command(BaseCommand):
    help = 'Populate database with initial subjects'

    def handle(self, *args, **kwargs):
        subjects_data = [
            {
                'title': 'Информатика',
                'icon': '💻',
                'color': '#3B82F6',  # Blue
            },
            {
                'title': 'Математика',
                'icon': '📐',
                'color': '#6366F1',  # Indigo
            },
            {
                'title': 'Русский язык',
                'icon': '📚',
                'color': '#EC4899',  # Pink
            },
            {
                'title': 'Физика',
                'icon': '⚛️',
                'color': '#8B5CF6',  # Purple
            },
        ]

        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                title=subject_data['title'],
                defaults={
                    'icon': subject_data['icon'],
                    'color': subject_data['color'],
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Создан предмет: {subject.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Предмет уже существует: {subject.title}')
                )

        self.stdout.write(self.style.SUCCESS('\n✓ Загрузка предметов завершена!'))
