from django.core.management.base import BaseCommand
from core.models import Task
import re


class Command(BaseCommand):
    help = 'Удаляет задания с неполным текстом (только "Вычислите:" без формулы)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать задания для удаления без фактического удаления'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        tasks = Task.objects.all()
        total = tasks.count()
        
        self.stdout.write(self.style.SUCCESS(f'🔍 Проверка {total} заданий...'))
        
        incomplete_tasks = []
        
        for task in tasks:
            if self.is_incomplete(task.question):
                incomplete_tasks.append(task)
        
        if not incomplete_tasks:
            self.stdout.write(self.style.SUCCESS('✅ Все задания корректны!'))
            return
        
        self.stdout.write(self.style.WARNING(f'\n⚠️  Найдено {len(incomplete_tasks)} неполных заданий:\n'))
        
        for task in incomplete_tasks[:10]:  # Показываем первые 10
            self.stdout.write(f'  #{task.id}: {task.question[:80]}...')
            if task.options:
                self.stdout.write(f'    Варианты: {", ".join(task.options.values())}')
        
        if len(incomplete_tasks) > 10:
            self.stdout.write(f'  ... и еще {len(incomplete_tasks) - 10} заданий')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 Режим просмотра (--dry-run). Задания НЕ удалены.'))
            self.stdout.write('Для удаления запустите без флага --dry-run')
        else:
            confirm = input(f'\nУдалить {len(incomplete_tasks)} заданий? (yes/no): ')
            if confirm.lower() == 'yes':
                for task in incomplete_tasks:
                    task.delete()
                self.stdout.write(self.style.SUCCESS(f'\n✅ Удалено {len(incomplete_tasks)} заданий'))
            else:
                self.stdout.write(self.style.WARNING('Отменено'))

    def is_incomplete(self, question):
        """Проверяет, является ли задание неполным"""
        if not question:
            return True
        
        # Убираем пробелы
        q = question.strip()
        
        # Паттерны неполных заданий
        incomplete_patterns = [
            r'^Вычислите:\s*$',
            r'^Найдите:\s*$',
            r'^Упростите:\s*$',
            r'^Решите:\s*$',
            r'^Определите:\s*$',
            r'^Найдите значение:\s*$',
            r'^Найдите значение выражения:\s*$',
            r'^Вычислите значение:\s*$',
        ]
        
        for pattern in incomplete_patterns:
            if re.match(pattern, q, re.IGNORECASE):
                return True
        
        # Проверяем, если вопрос слишком короткий (меньше 15 символов)
        if len(q) < 15:
            return True
        
        # Проверяем, если вопрос содержит только служебные слова
        words = q.split()
        if len(words) <= 2:
            return True
        
        return False
