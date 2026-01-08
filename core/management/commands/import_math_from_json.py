from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Subject, Topic, Task
import json
import os


class Command(BaseCommand):
    help = 'Импортирует математические тесты из JSON файла в БД'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Путь к JSON файлу с тестами'
        )
        parser.add_argument(
            '--subject',
            type=str,
            default=None,
            help='Название предмета (если не указано, берется из JSON)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие тесты и темы предмета перед импортом'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет импортировано без сохранения в БД'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        subject_name_override = options['subject']
        clear_existing = options['clear']
        dry_run = options['dry_run']

        # Проверяем существование файла
        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'❌ Файл не найден: {json_file}'))
            return

        # Читаем JSON
        self.stdout.write(self.style.SUCCESS(f'📖 Чтение данных из: {json_file}'))
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка чтения JSON: {e}'))
            return

        # Получаем название предмета
        subject_name = subject_name_override or data.get('subject')
        if not subject_name:
            self.stdout.write(self.style.ERROR('❌ Не указано название предмета'))
            return

        topics_data = data.get('topics', [])
        if not topics_data:
            self.stdout.write(self.style.ERROR('❌ В JSON нет данных о темах'))
            return

        # Подсчитываем статистику
        total_tasks = sum(len(topic.get('tasks', [])) for topic in topics_data)
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Статистика импорта:'))
        self.stdout.write(f'  Предмет: {subject_name}')
        self.stdout.write(f'  Тем: {len(topics_data)}')
        self.stdout.write(f'  Всего тестов: {total_tasks}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 Режим DRY-RUN (данные не будут сохранены)'))
            for topic_data in topics_data:
                topic_title = topic_data.get('title', 'Без названия')
                tasks_count = len(topic_data.get('tasks', []))
                self.stdout.write(f'  📁 {topic_title}: {tasks_count} тестов')
            return

        # Импортируем данные
        try:
            with transaction.atomic():
                # Получаем или создаем предмет
                subject, created = Subject.objects.get_or_create(
                    title=subject_name,
                    defaults={
                        'icon': '📐',
                        'color': '#4F6DF5'
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Создан предмет: {subject_name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'✅ Найден предмет: {subject_name}'))

                # Очищаем существующие данные если указан флаг
                if clear_existing:
                    deleted_tasks = Task.objects.filter(subject=subject).delete()[0]
                    deleted_topics = Topic.objects.filter(subject=subject).delete()[0]
                    self.stdout.write(self.style.WARNING(
                        f'🗑️  Удалено: {deleted_tasks} тестов, {deleted_topics} тем'
                    ))

                # Импортируем темы и тесты
                imported_topics = 0
                imported_tasks = 0
                skipped_tasks = 0
                total_topics = len(topics_data)
                
                self.stdout.write(self.style.SUCCESS(f'\n🚀 Начинаем импорт...'))
                self.stdout.write('=' * 70)
                
                for topic_idx, topic_data in enumerate(topics_data, 1):
                    topic_title = topic_data.get('title')
                    topic_order = topic_data.get('order', 0)
                    tasks_data = topic_data.get('tasks', [])
                    
                    if not topic_title:
                        self.stdout.write(self.style.WARNING('⚠️  Пропущена тема без названия'))
                        continue
                    
                    # Показываем прогресс по темам
                    self.stdout.write(f'\n📁 [{topic_idx}/{total_topics}] {topic_title}')
                    
                    # Создаем или получаем тему
                    topic, topic_created = Topic.objects.get_or_create(
                        subject=subject,
                        title=topic_title,
                        defaults={'order': topic_order}
                    )
                    
                    if topic_created:
                        imported_topics += 1
                        self.stdout.write(f'   ✅ Создана новая тема')
                    else:
                        self.stdout.write(f'   ℹ️  Тема уже существует')
                    
                    # Импортируем тесты для этой темы
                    topic_imported = 0
                    topic_skipped = 0
                    total_tasks_in_topic = len(tasks_data)
                    
                    for task_idx, task_data in enumerate(tasks_data, 1):
                        question = task_data.get('question')
                        options = task_data.get('options')
                        correct_answer = task_data.get('correct_answer')
                        difficulty = task_data.get('difficulty', 1)
                        original_test_id = task_data.get('original_test_id')
                        
                        # Показываем прогресс каждые 10 тестов или на последнем
                        if task_idx % 10 == 0 or task_idx == total_tasks_in_topic:
                            progress = (task_idx / total_tasks_in_topic) * 100
                            bar_length = 30
                            filled = int(bar_length * task_idx / total_tasks_in_topic)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            self.stdout.write(
                                f'\r   📊 [{bar}] {task_idx}/{total_tasks_in_topic} ({progress:.0f}%)',
                                ending=''
                            )
                            self.stdout.flush()
                        
                        if not question or not options or not correct_answer:
                            skipped_tasks += 1
                            topic_skipped += 1
                            continue
                        
                        # Проверяем, не существует ли уже такой тест
                        existing_task = Task.objects.filter(
                            subject=subject,
                            topic=topic,
                            original_test_id=original_test_id
                        ).first()
                        
                        if existing_task:
                            skipped_tasks += 1
                            topic_skipped += 1
                            continue
                        
                        # Создаем тест
                        task = Task.objects.create(
                            subject=subject,
                            topic=topic,
                            question=question,
                            options=options,
                            correct_answer=correct_answer,
                            difficulty=difficulty,
                            original_test_id=original_test_id,
                            order=imported_tasks
                        )
                        imported_tasks += 1
                        topic_imported += 1
                    
                    # Переход на новую строку после прогресс-бара
                    self.stdout.write('')
                    self.stdout.write(f'   ✅ Импортировано: {topic_imported} | ⏭️  Пропущено: {topic_skipped}')
                
                # Итоговая статистика
                self.stdout.write('\n' + '=' * 70)
                self.stdout.write(self.style.SUCCESS(f'✅ ИМПОРТ ЗАВЕРШЕН УСПЕШНО!'))
                self.stdout.write('=' * 70)
                self.stdout.write(f'\n📊 Итоговая статистика:')
                self.stdout.write(f'  📁 Создано новых тем: {imported_topics}')
                self.stdout.write(f'  📝 Импортировано тестов: {imported_tasks}')
                if skipped_tasks > 0:
                    self.stdout.write(f'  ⏭️  Пропущено тестов: {skipped_tasks}')
                self.stdout.write(f'  📚 Всего тем в предмете: {Topic.objects.filter(subject=subject).count()}')
                self.stdout.write(f'  📖 Всего тестов в предмете: {Task.objects.filter(subject=subject).count()}')
                self.stdout.write('\n' + '=' * 70)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при импорте: {e}'))
            raise
