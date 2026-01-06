"""
Генератор Open Graph изображений для задач
Создает красивые карточки 1200x630px с текстом вопроса
"""
from PIL import Image, ImageDraw, ImageFont
import textwrap
from io import BytesIO


def generate_task_og_image(task):
    """
    Генерирует OG-изображение для задачи
    
    Args:
        task: объект Task из Django модели
        
    Returns:
        BytesIO: буфер с PNG-изображением
    """
    # Размеры для Open Graph (рекомендация Facebook)
    width, height = 1200, 630
    
    # Создаем изображение с градиентным фоном
    img = Image.new('RGB', (width, height), color='#4F6DF5')
    draw = ImageDraw.Draw(img)
    
    # Рисуем градиент (от синего к фиолетовому)
    for y in range(height):
        ratio = y / height
        r = int(79 + (138 - 79) * ratio)
        g = int(109 + (43 - 109) * ratio)
        b = int(245 + (226 - 245) * ratio)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Добавляем полупрозрачный overlay для лучшей читаемости
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 50))
    img.paste(overlay, (0, 0), overlay)
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Пытаемся загрузить шрифты
    try:
        # Для заголовка (жирный)
        title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 48)
        # Для текста вопроса
        question_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
        # Для мелкого текста
        small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
    except:
        # Fallback на дефолтный шрифт если не найдены системные
        title_font = ImageFont.load_default()
        question_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Отступы
    padding = 60
    
    # Рисуем логотип/название сайта вверху
    site_name = "hushyor"
    draw.text((padding, padding), site_name, fill='white', font=title_font)
    
    # Рисуем предмет
    subject_text = f"Задание по {task.subject.title}"
    draw.text((padding, padding + 70), subject_text, fill='rgba(255, 255, 255, 0.9)', font=small_font)
    
    # Рисуем текст вопроса (с переносом строк)
    question_text = task.question
    # Ограничиваем длину вопроса
    if len(question_text) > 200:
        question_text = question_text[:197] + "..."
    
    # Разбиваем текст на строки
    max_chars_per_line = 45
    lines = textwrap.wrap(question_text, width=max_chars_per_line)
    
    # Ограничиваем количество строк
    max_lines = 8
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:40] + "..."
    
    # Рисуем вопрос
    y_offset = 200
    line_height = 50
    for line in lines:
        draw.text((padding, y_offset), line, fill='white', font=question_font)
        y_offset += line_height
    
    # Рисуем футер внизу
    footer_text = "Проверь свои знания на hushyor.com"
    footer_y = height - padding - 30
    draw.text((padding, footer_y), footer_text, fill='rgba(255, 255, 255, 0.8)', font=small_font)
    
    # Сохраняем в буфер
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    
    return buffer


def wrap_text(text, font, max_width, draw):
    """
    Вспомогательная функция для переноса текста по словам
    с учетом ширины шрифта
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines
