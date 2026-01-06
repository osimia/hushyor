"""
Django management command для очистки и импорта тестов
Использование: python manage.py clean_and_import_tests
"""

from django.core.management.base import BaseCommand
from core.models import Subject, Topic, Task
from django.db import connection
import json
import os


class Command(BaseCommand):
    help = 'Очищает старые Topics и Tasks, импортирует новые правильные данные'

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write("🔄 ОЧИСТКА И ИМПОРТ ДАННЫХ")
        self.stdout.write("=" * 70)
        
        # Шаг 1: Очистка
        if not self.clean_old_data():
            return
        
        # Шаг 2: Импорт
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("📥 ИМПОРТ НОВЫХ ДАННЫХ")
        self.stdout.write("=" * 70)
        
        self.import_new_data()
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("🎉 ВСЕ ГОТОВО!"))
        self.stdout.write("=" * 70)

    def clean_old_data(self):
        """Удаляет старые Topics и Tasks"""
        self.stdout.write("\n🧹 Очистка старых данных...")
        
        try:
            subject = Subject.objects.get(title="Забони тоҷикӣ")
            self.stdout.write(f"✅ Найден Subject: {subject.title} (ID: {subject.id})")
            
            old_topics_count = Topic.objects.filter(subject=subject).count()
            old_tasks_count = Task.objects.filter(subject=subject).count()
            
            self.stdout.write(f"\n📊 Будет удалено:")
            self.stdout.write(f"   Topics: {old_topics_count}")
            self.stdout.write(f"   Tasks: {old_tasks_count}")
            
            # Подтверждение
            self.stdout.write(f"\n⚠️  ВНИМАНИЕ! Это удалит все старые данные!")
            confirm = input("Продолжить? (yes/no): ")
            
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR("❌ Отменено пользователем"))
                return False
            
            # Удаляем Tasks
            self.stdout.write(f"\n🗑️  Удаление Tasks...")
            deleted_tasks = Task.objects.filter(subject=subject).delete()
            self.stdout.write(f"   ✅ Удалено Tasks: {deleted_tasks[0]}")
            
            # Удаляем Topics
            self.stdout.write(f"🗑️  Удаление Topics...")
            deleted_topics = Topic.objects.filter(subject=subject).delete()
            self.stdout.write(f"   ✅ Удалено Topics: {deleted_topics[0]}")
            
            # Сбрасываем sequences для Topic и Task
            self.stdout.write(f"\n🔄 Сброс PostgreSQL sequences...")
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT setval(pg_get_serial_sequence('core_topic', 'id'), 
                           COALESCE((SELECT MAX(id) FROM core_topic), 1), 
                           true);
                """)
                cursor.execute("""
                    SELECT setval(pg_get_serial_sequence('core_task', 'id'), 
                           COALESCE((SELECT MAX(id) FROM core_task), 1), 
                           true);
                """)
            self.stdout.write(f"   ✅ Sequences обновлены")
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Очистка завершена!"))
            return True
            
        except Subject.DoesNotExist:
            self.stdout.write(self.style.WARNING("⚠️  Subject 'Забони тоҷикӣ' не найден"))
            return False

    def import_new_data(self):
        """Импортирует новые данные"""
        tests_file = "test_database_fixed.json"
        answers_file = "answer_keys.json"
        
        self.stdout.write("\n📖 Читаю файлы...")
        
        if not os.path.exists(tests_file):
            self.stdout.write(self.style.ERROR(f"❌ Файл не найден: {tests_file}"))
            return
        
        if not os.path.exists(answers_file):
            self.stdout.write(self.style.ERROR(f"❌ Файл не найден: {answers_file}"))
            return
        
        with open(tests_file, 'r', encoding='utf-8') as f:
            tests = json.load(f)
        
        with open(answers_file, 'r', encoding='utf-8') as f:
            answers = json.load(f)
        
        self.stdout.write(f"📊 Загружено тестов: {len(tests)}")
        self.stdout.write(f"📊 Загружено ответов: {len(answers)}")
        
        # Получаем Subject
        subject = Subject.objects.get(title="Забони тоҷикӣ")
        self.stdout.write(f"\n✅ Используем Subject: {subject.title} (ID: {subject.id})")
        
        # Создаем Topics
        categories = {}
        for test in tests:
            cat = test['category']
            if cat not in categories:
                categories[cat] = len(categories)
        
        self.stdout.write(f"\n📂 Создание Topics ({len(categories)}):")
        
        topics_map = {}
        for category, order in categories.items():
            # Проверяем, существует ли уже такой Topic
            topic = Topic.objects.filter(subject=subject, title=category).first()
            if topic:
                self.stdout.write(f"   📌 Существует: {category}")
            else:
                # Создаем новый Topic без указания ID
                topic = Topic.objects.create(
                    subject=subject,
                    title=category,
                    order=order,
                    is_locked=False
                )
                self.stdout.write(f"   ✅ Создан: {category}")
            topics_map[category] = topic
        
        # Импортируем Tasks
        self.stdout.write(f"\n📝 Импорт тестов...")
        
        imported_count = 0
        skipped_count = 0
        no_answer_ids = []
        
        for test in tests:
            test_id = str(test['id'])
            
            # Пропускаем тесты с ID больше 919
            if test['id'] > 919:
                skipped_count += 1
                continue
            
            # Получаем ответ или оставляем пустым
            if test_id not in answers or not answers[test_id]:
                correct_answer = ''  # Пустой ответ для вопросов без ответа
                no_answer_ids.append(test['id'])
            else:
                correct_answer = answers[test_id]
            
            topic = topics_map.get(test['category'])
            
            options_json = {
                'A': test['options'].get('A', ''),
                'B': test['options'].get('B', ''),
                'C': test['options'].get('C', ''),
                'D': test['options'].get('D', ''),
            }
            
            if test.get('matching_options'):
                options_json['matching'] = {
                    'left': {k: v for k, v in test['matching_options'].items() if k in ['1','2','3','4']},
                    'right': {k: v for k, v in test['matching_options'].items() if k in ['A','B','C','D']}
                }
            
            difficulty_map = {
                'ФОНЕТИКА ва ҲОДИСАҲОИ ФОНЕТИКӢ': 1,
                'ИМЛО': 1,
                'ЛЕКСИКА': 1,
                'ФРАЗЕОЛОГИЯ': 2,
                'МОРФОЛОГИЯ': 2,
                'СИНТАКСИС': 3,
                'АДАБИЁТ': 3
            }
            difficulty = difficulty_map.get(test['category'], 1)
            
            Task.objects.create(
                subject=subject,
                topic=topic,
                question=test['question_text'],
                options=options_json,
                correct_answer=correct_answer,
                difficulty=difficulty,
                order=test['id'],
                original_test_id=test['id']
            )
            
            imported_count += 1
            
            if imported_count % 100 == 0:
                self.stdout.write(f"   📊 Импортировано: {imported_count}")
        
        # Статистика
        self.stdout.write(self.style.SUCCESS(f"\n✅ Импорт завершен!"))
        self.stdout.write(f"\n📊 Итоговая статистика:")
        self.stdout.write(f"   ✅ Импортировано: {imported_count}")
        self.stdout.write(f"   ⏭️  Пропущено (ID > 919): {skipped_count}")
        
        if no_answer_ids:
            self.stdout.write(f"\n⚠️  Тесты БЕЗ ответов (импортированы с пустым correct_answer):")
            self.stdout.write(f"   Количество: {len(no_answer_ids)}")
            self.stdout.write(f"   ID: {', '.join(map(str, no_answer_ids))}")
        
        # Проверка
        self.stdout.write(f"\n🔍 Проверка в БД:")
        self.stdout.write(f"   Topics: {Topic.objects.filter(subject=subject).count()}")
        self.stdout.write(f"   Tasks: {Task.objects.filter(subject=subject).count()}")
        
        self.stdout.write(f"\n📊 Распределение по категориям:")
        for topic in Topic.objects.filter(subject=subject).order_by('order'):
            count = Task.objects.filter(topic=topic).count()
            self.stdout.write(f"   {topic.title}: {count}")
