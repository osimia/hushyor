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
    
    # Создаем изображение с красивым градиентным фоном
    # Мягкий градиент от светло-голубого к белому
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Создаем вертикальный градиент (сверху вниз)
    for y in range(height):
        ratio = y / height
        # Плавный переход от светло-голубого к почти белому
        r = int(240 + (250 - 240) * ratio)
        g = int(245 + (252 - 245) * ratio)
        b = int(252 + (255 - 252) * ratio)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    draw = ImageDraw.Draw(img)
    
    # Загружаем шрифты с поддержкой таджикского языка
    title_font = None
    question_font = None
    small_font = None
    
    # Приоритет шрифтов: используем обычный DejaVu Sans (не Bold) для более легкого вида
    font_paths = [
        # Шрифты из core/fonts/ - приоритет обычному шрифту, не жирному
        os.path.join(settings.BASE_DIR, 'core', 'fonts', 'DejaVuSans.ttf'),
        os.path.join(settings.BASE_DIR, 'core', 'fonts', 'DejaVuSans-Bold.ttf'),
        # Системные шрифты DejaVu (Linux)
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        # macOS
        '/System/Library/Fonts/Supplemental/DejaVuSans.ttf',
        '/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf',
        # Windows
        'C:\\Windows\\Fonts\\DejaVuSans.ttf',
        'C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf',
    ]
    
    font_loaded = False
    loaded_font_path = None
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                # Используем тонкий шрифт и меньшие размеры для элегантности
                title_font = ImageFont.truetype(font_path, 28)  # Уменьшен
                question_font = ImageFont.truetype(font_path, 26)  # Уменьшен
                small_font = ImageFont.truetype(font_path, 22)  # Уменьшен
                font_loaded = True
                loaded_font_path = font_path  # Сохраняем путь для использования позже
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
    
    # Очищаем текст вопроса от HTML-тегов
    question_text = strip_tags(task.question)
    
    # Ограничиваем длину вопроса (меньше, чтобы оставить место для вариантов)
    if len(question_text) > 120:
        question_text = question_text[:117] + "..."
    
    # Разбиваем текст на строки с учетом ширины
    max_chars_per_line = 40
    lines = textwrap.wrap(question_text, width=max_chars_per_line, break_long_words=False, break_on_hyphens=False)
    
    # Ограничиваем количество строк вопроса
    max_lines = 3
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if len(lines[-1]) > 35:
            lines[-1] = lines[-1][:32] + "..."
    
    # Рисуем вопрос (темный текст на светлом фоне)
    y_offset = 80
    line_height = 45
    for line in lines:
        draw.text((padding, y_offset), line, fill=(30, 35, 50), font=question_font)
        y_offset += line_height
    
    # Добавляем отступ после вопроса
    y_offset += 30
    
    # Рисуем варианты ответов (если есть)
    if task.options:
        import json
        try:
            # Парсим варианты ответов
            if isinstance(task.options, str):
                options = json.loads(task.options)
            else:
                options = task.options
            
            # Создаем очень тонкий шрифт для вариантов
            option_font = ImageFont.truetype(loaded_font_path, 24) if font_loaded and loaded_font_path else small_font
            
            # Рисуем каждый вариант с фоном
            for key in sorted(options.keys())[:4]:  # Максимум 4 варианта
                value = strip_tags(str(options[key]))
                
                # Ограничиваем длину варианта
                if len(value) > 50:
                    value = value[:47] + "..."
                
                # Создаем более тонкие закругленные блоки
                box_height = 42  # Уменьшена высота
                box_width = width - (padding * 2)
                
                # Более светлый синий цвет для блоков
                blue_color = (103, 128, 245)  # Чуть светлее для элегантности
                
                # Рисуем закругленный блок с синим фоном
                draw.rounded_rectangle(
                    [(padding, y_offset - 6), (padding + box_width, y_offset + box_height - 6)],
                    radius=21,  # Чуть меньший радиус для пропорциональности
                    fill=blue_color
                )
                
                # Рисуем текст варианта белым цветом на синем фоне
                option_text = f"{key}. {value}"
                draw.text((padding + 16, y_offset), option_text, fill=(255, 255, 255, 240), font=option_font)
                y_offset += box_height + 15  # Отступ между вариантами
                
        except Exception as e:
            logger.warning(f"Failed to parse options: {str(e)}")
    
    # Футер убран - не показываем текст внизу
    
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
