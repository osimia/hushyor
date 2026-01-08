"""
Django management command для исправления конкретных проблемных формул
"""

from django.core.management.base import BaseCommand
from core.models import Task
import json


class Command(BaseCommand):
    help = 'Исправляет конкретные проблемные формулы из оригинального JSON'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Исправление проблемных формул из JSON...')
        self.stdout.write('=' * 70)
        
        # Читаем правильные данные из JSON
        with open('math_tests_import.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Создаем словарь правильных вопросов по original_test_id
        correct_questions = {}
        for topic in data['topics']:
            for task in topic['tasks']:
                test_id = task.get('original_test_id')
                if test_id:
                    correct_questions[test_id] = task.get('question')
        
        self.stdout.write(f'\n📊 Загружено {len(correct_questions)} правильных вопросов из JSON')
        
        # Получаем все тесты по математике из БД
        math_tasks = Task.objects.filter(subject_id=2)
        
        fixed_count = 0
        
        for task in math_tasks:
            if task.original_test_id in correct_questions:
                correct_question = correct_questions[task.original_test_id]
                
                # Проверяем, отличается ли вопрос в БД от правильного
                if task.question != correct_question:
                    # Обновляем вопрос
                    task.question = correct_question
                    task.save(update_fields=['question'])
                    fixed_count += 1
                    
                    if fixed_count <= 10:  # Показываем первые 10 исправлений
                        self.stdout.write(f'  ✅ Исправлен тест #{task.original_test_id}')
        
        # Итоговая статистика
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'\n📊 Статистика:')
        self.stdout.write(f'  ✅ Исправлено тестов: {fixed_count}')
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('\n💡 Обновите страницу в браузере (Ctrl+Shift+R)')
