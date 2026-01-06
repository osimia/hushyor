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
    
    # Создаем изображение с чистым белым фоном
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Добавляем декоративные элементы - очень светлые круги в углах
    # Верхний правый угол - светло-голубой круг
    draw.ellipse([900, -100, 1300, 300], fill=(230, 235, 250))
    # Нижний левый угол - светло-фиолетовый круг
    draw.ellipse([-100, 400, 300, 800], fill=(245, 235, 250))
    
    # Загружаем шрифты с поддержкой таджикского языка
    title_font = None
    question_font = None
    small_font = None
    
    # Приоритет шрифтов: используем обычный DejaVu Sans для читабельности
    font_paths = [
        # Шрифты из core/fonts/
        os.path.join(settings.BASE_DIR, 'core', 'fonts', 'DejaVuSans.ttf'),
        os.path.join(settings.BASE_DIR, 'core', 'fonts', 'DejaVuSans-Bold.ttf'),
        # Системные шрифты DejaVu (Linux)
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        # macOS
        '/System/Library/Fonts/Supplemental/DejaVuSans.ttf',
        # Windows
        'C:\\Windows\\Fonts\\DejaVuSans.ttf',
    ]
    
    bold_font_paths = [
        os.path.join(settings.BASE_DIR, 'core', 'fonts', 'DejaVuSans-Bold.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/System/Library/Fonts/Supplemental/DejaVuSans-Bold.ttf',
        'C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf',
    ]
    
    font_loaded = False
    loaded_font_path = None
    loaded_bold_font_path = None
    
    # Загружаем обычный шрифт
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                question_font = ImageFont.truetype(font_path, 32)  # Для вопроса
                small_font = ImageFont.truetype(font_path, 26)  # Для вариантов
                font_loaded = True
                loaded_font_path = font_path
                logger.info(f"Successfully loaded regular font from: {font_path}")
                break
        except Exception as e:
            logger.warning(f"Failed to load font from {font_path}: {str(e)}")
            continue
    
    # Загружаем жирный шрифт для заголовка
    for bold_path in bold_font_paths:
        try:
            if os.path.exists(bold_path):
                title_font = ImageFont.truetype(bold_path, 36)  # Жирный для бренда
                loaded_bold_font_path = bold_path
                logger.info(f"Successfully loaded bold font from: {bold_path}")
                break
        except Exception as e:
            logger.warning(f"Failed to load bold font from {bold_path}: {str(e)}")
            continue
    
    # Если жирный не загрузился, используем обычный
    if not loaded_bold_font_path and loaded_font_path:
        title_font = ImageFont.truetype(loaded_font_path, 36)
    
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
    padding = 70
    
    # Добавляем логотип/бренд вверху
    brand_y = 40
    draw.text((padding, brand_y), "hushyor", fill=(79, 109, 245), font=title_font)
    
    # Добавляем тонкую линию под брендом
    line_y = brand_y + 50
    draw.rectangle([(padding, line_y), (padding + 120, line_y + 3)], fill=(79, 109, 245))
    
    # Очищаем текст вопроса от HTML-тегов
    question_text = strip_tags(task.question)
    
    # Ограничиваем длину вопроса
    if len(question_text) > 150:
        question_text = question_text[:147] + "..."
    
    # Разбиваем текст на строки с учетом ширины
    max_chars_per_line = 55
    lines = textwrap.wrap(question_text, width=max_chars_per_line, break_long_words=False, break_on_hyphens=False)
    
    # Ограничиваем количество строк вопроса
    max_lines = 3
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if len(lines[-1]) > 50:
            lines[-1] = lines[-1][:47] + "..."
    
    # Рисуем вопрос (темно-серый текст)
    y_offset = line_y + 40
    line_height = 50
    for line in lines:
        draw.text((padding, y_offset), line, fill=(30, 35, 50), font=question_font)
        y_offset += line_height
    
    # Добавляем отступ после вопроса
    y_offset += 25
    
    # Рисуем варианты ответов (если есть)
    if task.options:
        import json
        try:
            # Парсим варианты ответов
            if isinstance(task.options, str):
                options = json.loads(task.options)
            else:
                options = task.options
            
            # Рисуем каждый вариант с современным дизайном
            for key in sorted(options.keys())[:4]:  # Максимум 4 варианта
                value = strip_tags(str(options[key]))
                
                # Ограничиваем длину варианта
                if len(value) > 60:
                    value = value[:57] + "..."
                
                # Параметры блока
                box_height = 50
                box_width = width - (padding * 2)
                
                # Белый блок с тенью (эффект карточки)
                # Тень
                shadow_offset = 3
                draw.rounded_rectangle(
                    [(padding + shadow_offset, y_offset + shadow_offset), 
                     (padding + box_width + shadow_offset, y_offset + box_height + shadow_offset)],
                    radius=12,
                    fill=(200, 200, 210, 50)
                )
                
                # Основной блок
                draw.rounded_rectangle(
                    [(padding, y_offset), (padding + box_width, y_offset + box_height)],
                    radius=12,
                    fill=(255, 255, 255),
                    outline=(220, 225, 235),
                    width=2
                )
                
                # Цветной круг с буквой варианта
                circle_x = padding + 20
                circle_y = y_offset + 25
                circle_radius = 18
                
                # Градиентный цвет для каждого варианта
                colors = {
                    'A': (79, 109, 245),   # Синий
                    'B': (99, 179, 237),   # Голубой
                    'C': (168, 85, 247),   # Фиолетовый
                    'D': (236, 72, 153)    # Розовый
                }
                circle_color = colors.get(key, (79, 109, 245))
                
                draw.ellipse(
                    [(circle_x - circle_radius, circle_y - circle_radius),
                     (circle_x + circle_radius, circle_y + circle_radius)],
                    fill=circle_color
                )
                
                # Буква варианта белым цветом в круге
                # Центрируем букву в круге
                letter_bbox = draw.textbbox((0, 0), key, font=small_font)
                letter_width = letter_bbox[2] - letter_bbox[0]
                letter_height = letter_bbox[3] - letter_bbox[1]
                letter_x = circle_x - letter_width // 2
                letter_y = circle_y - letter_height // 2 - 3
                
                draw.text((letter_x, letter_y), key, fill=(255, 255, 255), font=small_font)
                
                # Текст варианта
                text_x = circle_x + circle_radius + 15
                text_y = y_offset + 12
                draw.text((text_x, text_y), value, fill=(50, 55, 70), font=small_font)
                
                y_offset += box_height + 12  # Отступ между вариантами
                
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
