import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Настройка Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.core.management import call_command
from django.db import transaction
from core.models import Subject, Topic, Task

def print_progress_bar(current, total, prefix='', suffix='', length=50):
    """Выводит прогресс-бар в консоль"""
    percent = 100 * (current / float(total))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '░' * (length - filled_length)
    
    print(f'\r{prefix} |{bar}| {current}/{total} ({percent:.1f}%) {suffix}', end='', flush=True)
    
    if current == total:
        print()

def import_data_with_progress(json_file):
    """Импортирует данные из JSON с отображением прогресса"""
    
    print("=" * 80)
    print("📦 ИМПОРТ ДАННЫХ В БАЗУ ДАННЫХ")
    print("=" * 80)
    
    if not json_file.exists():
        print(f"❌ Файл не найден: {json_file}")
        return
    
    print(f"\n📂 Загрузка файла: {json_file.name}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_records = len(data)
    print(f"✅ Загружено {total_records} записей из JSON")
    
    # Группируем данные по моделям
    subjects = [item for item in data if item['model'] == 'core.subject']
    topics = [item for item in data if item['model'] == 'core.topic']
    tasks = [item for item in data if item['model'] == 'core.task']
    
    print(f"\n📊 Статистика:")
    print(f"   • Предметы (Subject): {len(subjects)}")
    print(f"   • Темы (Topic): {len(topics)}")
    print(f"   • Задания (Task): {len(tasks)}")
    
    # Проверяем существующие данные
    existing_subjects = Subject.objects.count()
    existing_topics = Topic.objects.count()
    existing_tasks = Task.objects.count()
    
    if existing_subjects > 0 or existing_topics > 0 or existing_tasks > 0:
        print(f"\n⚠️  В базе уже есть данные:")
        print(f"   • Предметы: {existing_subjects}")
        print(f"   • Темы: {existing_topics}")
        print(f"   • Задания: {existing_tasks}")
        
        response = input("\n❓ Очистить базу перед импортом? (yes/no): ").strip().lower()
        
        if response in ['yes', 'y', 'да', 'д']:
            print("\n🗑️  Очистка базы данных...")
            Task.objects.all().delete()
            Topic.objects.all().delete()
            Subject.objects.all().delete()
            print("✅ База очищена")
        else:
            print("⚠️  Импорт будет выполнен с существующими данными (возможны конфликты)")
    
    print("\n" + "=" * 80)
    print("🚀 НАЧАЛО ИМПОРТА")
    print("=" * 80)
    
    start_time = datetime.now()
    
    try:
        with transaction.atomic():
            # Импорт предметов
            if subjects:
                print("\n📚 Импорт предметов...")
                for i, item in enumerate(subjects, 1):
                    fields = item['fields']
                    Subject.objects.update_or_create(
                        pk=item['pk'],
                        defaults={
                            'title': fields['title'],
                            'icon': fields['icon'],
                            'color': fields['color']
                        }
                    )
                    print_progress_bar(i, len(subjects), prefix='Предметы', suffix='')
            
            # Импорт тем
            if topics:
                print("\n📖 Импорт тем...")
                for i, item in enumerate(topics, 1):
                    fields = item['fields']
                    Topic.objects.update_or_create(
                        pk=item['pk'],
                        defaults={
                            'subject_id': fields['subject'],
                            'title': fields['title'],
                            'order': fields['order'],
                            'is_locked': fields['is_locked']
                        }
                    )
                    print_progress_bar(i, len(topics), prefix='Темы', suffix='')
            
            # Импорт заданий
            if tasks:
                print("\n📝 Импорт заданий...")
                batch_size = 100
                
                for i, item in enumerate(tasks, 1):
                    fields = item['fields']
                    Task.objects.update_or_create(
                        pk=item['pk'],
                        defaults={
                            'subject_id': fields['subject'],
                            'topic_id': fields['topic'],
                            'question': fields['question'],
                            'options': fields['options'],
                            'correct_answer': fields['correct_answer'],
                            'difficulty': fields['difficulty'],
                            'order': fields['order']
                        }
                    )
                    
                    # Показываем прогресс
                    print_progress_bar(i, len(tasks), prefix='Задания', suffix='')
                    
                    # Периодически выводим статистику
                    if i % batch_size == 0:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        speed = i / elapsed if elapsed > 0 else 0
                        remaining = (len(tasks) - i) / speed if speed > 0 else 0
                        print(f" | Скорость: {speed:.1f} зап/сек | Осталось: ~{remaining:.0f}сек", end='')
        
        # Финальная статистика
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n\n" + "=" * 80)
        print("✅ ИМПОРТ ЗАВЕРШЕН УСПЕШНО!")
        print("=" * 80)
        
        print(f"\n📊 Итоговая статистика:")
        print(f"   • Предметы: {Subject.objects.count()}")
        print(f"   • Темы: {Topic.objects.count()}")
        print(f"   • Задания: {Task.objects.count()}")
        
        print(f"\n⏱️  Время выполнения: {duration:.2f} секунд")
        print(f"⚡ Средняя скорость: {total_records/duration:.1f} записей/сек")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n\n❌ ОШИБКА ПРИ ИМПОРТЕ: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    json_file = Path(__file__).parent / 'hushyor_data.json'
    
    success = import_data_with_progress(json_file)
    
    if success:
        print("\n🎉 Данные успешно импортированы!")
        print("\n💡 Следующие шаги:")
        print("   1. Создайте суперпользователя: python manage.py createsuperuser")
        print("   2. Запустите сервер: python manage.py runserver")
    else:
        print("\n❌ Импорт завершился с ошибками")
        sys.exit(1)

if __name__ == '__main__':
    main()
