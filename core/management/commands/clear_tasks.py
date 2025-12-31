from django.core.management.base import BaseCommand
from core.models import Task, Topic, Subject


class Command(BaseCommand):
    help = 'Очищает все задания и темы из базы данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Подтверждение удаления без запроса'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            confirm = input('Вы уверены, что хотите удалить ВСЕ задания и темы? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Отменено'))
                return
        
        # Подсчитываем количество
        task_count = Task.objects.count()
        topic_count = Topic.objects.count()
        
        # Удаляем
        Task.objects.all().delete()
        Topic.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'✅ Удалено {task_count} заданий'))
        self.stdout.write(self.style.SUCCESS(f'✅ Удалено {topic_count} тем'))
        self.stdout.write(self.style.SUCCESS('✅ База данных очищена!'))
