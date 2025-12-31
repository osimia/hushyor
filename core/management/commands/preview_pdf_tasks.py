from django.core.management.base import BaseCommand
import re
import PyPDF2


class Command(BaseCommand):
    help = 'Предпросмотр заданий из PDF файла перед импортом'

    def add_arguments(self, parser):
        parser.add_argument('pdf_file', type=str, help='Путь к PDF файлу')
        parser.add_argument('--limit', type=int, default=5, help='Количество заданий для показа')

    def handle(self, *args, **options):
        pdf_path = options['pdf_file']
        limit = options['limit']
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("📖 ПРЕДПРОСМОТР PDF ФАЙЛА"))
        self.stdout.write("="*80 + "\n")
        
        # Извлекаем текст из PDF
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text:
            self.stdout.write(self.style.ERROR("❌ Не удалось извлечь текст из PDF"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"✅ Извлечено {len(text)} символов\n"))
        
        # Показываем первые 500 символов
        self.stdout.write("-"*80)
        self.stdout.write(self.style.WARNING("ПЕРВЫЕ 500 СИМВОЛОВ:"))
        self.stdout.write("-"*80)
        self.stdout.write(text[:500])
        self.stdout.write("-"*80 + "\n")
        
        # Парсим задания
        self.stdout.write(self.style.SUCCESS("🔍 Парсинг заданий..."))
        tasks = self.parse_tasks_from_text(text)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Найдено {len(tasks)} заданий\n"))
        
        if not tasks:
            self.stdout.write(self.style.WARNING("⚠️  Задания не найдены. Проверьте формат PDF."))
            return
        
        # Показываем статистику
        self.show_statistics(tasks)
        
        # Показываем примеры заданий
        self.show_task_examples(tasks[:limit])
        
        # Спрашиваем подтверждение
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.WARNING("Данные выглядят корректно?"))
        self.stdout.write("Для импорта запустите:")
        self.stdout.write(self.style.SUCCESS(f"python manage.py import_pdf_tasks {pdf_path}"))
        self.stdout.write("="*80 + "\n")

    def extract_text_from_pdf(self, pdf_path):
        """Извлекает текст из PDF файла"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при чтении PDF: {e}"))
        return text

    def parse_tasks_from_text(self, text):
        """Парсит задания из текста"""
        tasks = []
        current_topic = "Действия с рациональными и иррациональными числами"
        
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ищем начало задания
            match = re.match(r'^(\d+)\s+(.+)', line)
            if match:
                task_number = match.group(1)
                question_start = match.group(2)
                
                # Собираем полный вопрос
                question_lines = [question_start]
                i += 1
                
                # Читаем до варианта A)
                while i < len(lines) and not re.match(r'^\s*[ABCDАБВГД]\)', lines[i]):
                    if lines[i].strip() and not re.match(r'^\d+\s+', lines[i]):
                        question_lines.append(lines[i].strip())
                    i += 1
                
                question = ' '.join(question_lines).strip()
                
                # Парсим варианты ответов
                options = {}
                option_letters = ['A', 'B', 'C', 'D']
                
                for option_letter in option_letters:
                    if i < len(lines):
                        option_match = re.match(rf'^\s*[{option_letter}АБВГ]\)\s*(.+)', lines[i])
                        if option_match:
                            options[option_letter] = option_match.group(1).strip()
                            i += 1
                
                # Проверяем, что все варианты найдены
                if len(options) == 4 and question:
                    tasks.append({
                        'number': task_number,
                        'question': question,
                        'options': options,
                        'topic': current_topic
                    })
            else:
                # Проверяем, не новая ли тема
                if re.match(r'^[А-ЯЁ\s]{10,}$', line):
                    current_topic = line.strip()
                i += 1
        
        return tasks

    def show_statistics(self, tasks):
        """Показывает статистику по заданиям"""
        # Группируем по темам
        topics = {}
        for task in tasks:
            topic = task['topic']
            if topic not in topics:
                topics[topic] = 0
            topics[topic] += 1
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("📊 СТАТИСТИКА ПО ТЕМАМ"))
        self.stdout.write("="*80)
        
        for topic, count in topics.items():
            self.stdout.write(f"  • {topic}: {count} заданий")
        
        self.stdout.write("-"*80)
        self.stdout.write(self.style.SUCCESS(f"  ВСЕГО: {len(tasks)} заданий"))
        self.stdout.write("="*80 + "\n")

    def show_task_examples(self, tasks):
        """Показывает примеры заданий"""
        self.stdout.write(self.style.SUCCESS(f"📝 ПРИМЕРЫ ЗАДАНИЙ (первые {len(tasks)}):\n"))
        
        for idx, task in enumerate(tasks, 1):
            self.stdout.write("="*80)
            self.stdout.write(self.style.WARNING(f"ЗАДАНИЕ #{task['number']}"))
            self.stdout.write("="*80)
            
            self.stdout.write(f"\n{self.style.HTTP_INFO('Вопрос:')} {task['question']}\n")
            self.stdout.write(f"{self.style.SUCCESS('A)')} {task['options']['A']}")
            self.stdout.write(f"{self.style.SUCCESS('B)')} {task['options']['B']}")
            self.stdout.write(f"{self.style.SUCCESS('C)')} {task['options']['C']}")
            self.stdout.write(f"{self.style.SUCCESS('D)')} {task['options']['D']}")
            self.stdout.write(f"\n{self.style.MIGRATE_LABEL('Тема:')} {task['topic']}\n")
            
            if idx < len(tasks):
                self.stdout.write("")
