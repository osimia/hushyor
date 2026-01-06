"""
Генератор Open Graph изображений для задач
Создает красивые карточки 1200x630px с текстом вопроса
"""
from PIL import Image, ImageDraw, ImageFont
import textwrap
from io import BytesIO
import os
import logging
from django.conf import settings
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def generate_task_og_image(task):
    """
    Генерирует OG-изображение для задачи с поддержкой таджикского языка
    
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
    
    # Загружаем шрифты с поддержкой таджикского языка
    title_font = None
    question_font = None
    small_font = None
    
    # Приоритет шрифтов: DejaVu Sans поддерживает таджикские символы (ҳ, ҷ, ӣ, ӯ, қ, ғ)
    font_paths = [
        # Шрифты из core/fonts/ (используем settings.BASE_DIR)
        os.path.join(settings.BASE_DIR, 'core', 'fonts', 'DejaVuSans-Bold.ttf'),
        os.path.join(settings.BASE_DIR, 'core', 'fonts', 'DejaVuSans.ttf'),
        # Системные шрифты DejaVu (Linux)
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        # macOS
        '/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf',
        '/System/Library/Fonts/Supplemental/DejaVuSans.ttf',
        # Windows
        'C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf',
        'C:\\Windows\\Fonts\\DejaVuSans.ttf',
    ]
    
    font_loaded = False
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                title_font = ImageFont.truetype(font_path, 48)
                question_font = ImageFont.truetype(font_path, 36)
                small_font = ImageFont.truetype(font_path, 28)
                font_loaded = True
                logger.info(f"Successfully loaded font from: {font_path}")
                break
        except Exception as e:
            logger.warning(f"Failed to load font from {font_path}: {str(e)}")
            continue
    
    # Если не нашли ни один шрифт - используем встроенный (но он не поддерживает таджикский)
    if not font_loaded:
        logger.error("No suitable font found! Tajik characters may not display correctly.")
        try:
            title_font = ImageFont.load_default()
            question_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        except Exception as e:
            logger.error(f"Failed to load default font: {str(e)}")
            # Последний fallback - None (PIL будет использовать базовый)
            title_font = None
            question_font = None
            small_font = None
    
    # Отступы
    padding = 60
    
    # Рисуем логотип/название сайта вверху
    site_name = "hushyor"
    draw.text((padding, padding), site_name, fill='white', font=title_font)
    
    # Рисуем предмет
    subject_text = f"Задание по {task.subject.title}"
    draw.text((padding, padding + 70), subject_text, fill=(255, 255, 255, 230), font=small_font)
    
    # Очищаем текст вопроса от HTML-тегов
    question_text = strip_tags(task.question)
    
    # Ограничиваем длину вопроса
    if len(question_text) > 250:
        question_text = question_text[:247] + "..."
    
    # Разбиваем текст на строки с учетом ширины (35-40 символов для таджикского текста)
    max_chars_per_line = 38
    lines = textwrap.wrap(question_text, width=max_chars_per_line, break_long_words=False, break_on_hyphens=False)
    
    # Ограничиваем количество строк
    max_lines = 8
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if len(lines[-1]) > 35:
            lines[-1] = lines[-1][:32] + "..."
    
    # Рисуем вопрос
    y_offset = 200
    line_height = 50
    for line in lines:
        draw.text((padding, y_offset), line, fill='white', font=question_font)
        y_offset += line_height
    
    # Рисуем футер внизу
    footer_text = "Проверь свои знания на hushyor.com"
    footer_y = height - padding - 30
    draw.text((padding, footer_y), footer_text, fill=(255, 255, 255, 204), font=small_font)
    
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
