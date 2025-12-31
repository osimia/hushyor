from django.core.management.base import BaseCommand
from core.models import Task
import re


class Command(BaseCommand):
    help = 'Очищает математические символы в уже импортированных заданиях'

    def handle(self, *args, **options):
        tasks = Task.objects.all()
        total = tasks.count()
        
        self.stdout.write(self.style.SUCCESS(f'🔍 Найдено {total} заданий для очистки'))
        
        updated_count = 0
        
        for task in tasks:
            original_question = task.question
            original_options = task.options.copy() if task.options else {}
            
            # Очищаем вопрос
            cleaned_question = self.clean_math_text(original_question)
            
            # Очищаем варианты ответов
            cleaned_options = {}
            if task.options:
                for key, value in task.options.items():
                    cleaned_options[key] = self.clean_math_text(value)
            
            # Проверяем, изменилось ли что-то
            if cleaned_question != original_question or cleaned_options != original_options:
                task.question = cleaned_question
                task.options = cleaned_options
                task.save()
                updated_count += 1
                
                if updated_count <= 5:  # Показываем первые 5 примеров
                    self.stdout.write(f'\n✓ Задание #{task.id}:')
                    self.stdout.write(f'  Было: {original_question[:60]}...')
                    self.stdout.write(f'  Стало: {cleaned_question[:60]}...')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Обновлено {updated_count} из {total} заданий'))

    def clean_math_text(self, text):
        """Очищает математические символы"""
        if not text:
            return text
        
        # Словарь замен
        replacements = {
            # Скобки
            'ሺ': '(',
            'ሻ': ')',
            '൫': '(',
            '൯': ')',
            
            # Математические операторы
            'ൌ': '=',
            '൅': '+',
            'െ': '-',
            '∙': '·',
            '⋅': '·',
            '×': '·',
            
            # Корни
            'ට': '√',
            '√': '√',
            
            # Дроби и степени
            '⁄': '/',
            '∶': ':',
            '÷': ':',
            
            # Буквы (математические шрифты)
            '𝒙': 'x',
            '𝒚': 'y',
            '𝒛': 'z',
            '𝒇': 'f',
            '𝒈': 'g',
            '𝒂': 'a',
            '𝒃': 'b',
            '𝒄': 'c',
            '𝒅': 'd',
            '𝒏': 'n',
            '𝒎': 'm',
            '𝒑': 'p',
            '𝒒': 'q',
            '𝒓': 'r',
            '𝒔': 's',
            '𝒕': 't',
            
            # Заглавные буквы
            '𝑨': 'A',
            '𝑩': 'B',
            '𝑪': 'C',
            '𝑫': 'D',
            '𝑬': 'E',
            '𝑭': 'F',
            '𝑮': 'G',
            '𝑯': 'H',
            '𝑰': 'I',
            '𝑱': 'J',
            '𝑲': 'K',
            '𝑳': 'L',
            '𝑴': 'M',
            '𝑵': 'N',
            '𝑶': 'O',
            '𝑷': 'P',
            '𝑸': 'Q',
            '𝑹': 'R',
            '𝑺': 'S',
            '𝑻': 'T',
            '𝑼': 'U',
            '𝑽': 'V',
            '𝑾': 'W',
            '𝑿': 'X',
            '𝒀': 'Y',
            '𝒁': 'Z',
            
            # Цифры (математические шрифты)
            '𝟎': '0',
            '𝟏': '1',
            '𝟐': '2',
            '𝟑': '3',
            '𝟒': '4',
            '𝟓': '5',
            '𝟔': '6',
            '𝟕': '7',
            '𝟖': '8',
            '𝟗': '9',
            
            # Греческие буквы
            '𝛂': 'α',
            '𝛃': 'β',
            '𝛄': 'γ',
            '𝛅': 'δ',
            '𝛆': 'ε',
            '𝛇': 'ζ',
            '𝛈': 'η',
            '𝛉': 'θ',
            
            # Пробелы и разделители
            ' ': ' ',  # Неразрывный пробел
            ',': ',',
        }
        
        # Применяем все замены
        cleaned = text
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Убираем множественные пробелы
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Убираем пробелы перед знаками препинания
        cleaned = re.sub(r'\s+([,.:;!?])', r'\1', cleaned)
        
        return cleaned.strip()
