import os
import google.generativeai as genai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY and GEMINI_API_KEY != 'your-gemini-api-key-here':
    genai.configure(api_key=GEMINI_API_KEY)

def get_theory_lesson(task_question, task_subject, language='ru'):
    """
    Генерирует короткий урок с теорией и примерами для задачи
    language: 'ru' для русского, 'tg' для таджикского
    """
    import logging
    import hashlib
    from django.core.cache import cache
    
    logger = logging.getLogger(__name__)
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        logger.warning("Gemini API key not configured")
        return "⚠️ API ключ Gemini не настроен. Добавьте GEMINI_API_KEY в файл .env"
    
    # Кэширование ответов с учетом языка
    cache_key = hashlib.md5(f"theory_{task_question}_{task_subject}_{language}".encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Returning cached theory for {task_subject} in {language}")
        return cached
    
    try:
        logger.info(f"Generating theory lesson for subject: {task_subject} in language: {language}")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Выбираем язык для промпта
        if language == 'tg':
            prompt = f"""Шумо омӯзгори ботаҷриба аз фанни "{task_subject}" ҳастед. Хонанда барои имтиҳон омода мешавад ва вақти зиёд надорад.

Масъала: {task_question}

Дарси ХЕЛЕ КӮТОҲ эҷод кунед (МАКСИМУМ 5-6 САТР):

📌 Асос: [1 ҷумла - консепсияи асосӣ]

💡 Мисол: [1 мисоли кӯтоҳ бо ҳалл]

✅ Тарзи ҳал: [1-2 ҷумла - қадамҳои асосӣ]

МУҲИМ: Кӯтоҳ ва равшан нависед! Хонанда вақт надорад."""
        else:
            prompt = f"""Ты - преподаватель по предмету "{task_subject}". Ученик готовится к экзамену и у него мало времени.

Задача: {task_question}

Создай ОЧЕНЬ КРАТКУЮ теорию (МАКСИМУМ 5-6 СТРОК):

📌 Суть: [1 предложение - основная концепция]

💡 Пример: [1 короткий пример с решением]

✅ Как решать: [1-2 предложения - основные шаги]

ВАЖНО: Пиши кратко и понятно! У ученика нет времени на длинные тексты."""

        response = model.generate_content(prompt)
        result = response.text
        
        # Кэшируем на 24 часа
        cache.set(cache_key, result, 86400)
        logger.info("Theory lesson generated successfully")
        return result
    
    except Exception as e:
        logger.error(f"Error generating theory: {e}", exc_info=True)
        return f"⚠️ Ошибка при генерации теории. Попробуйте позже."


def get_hint(task_question, task_subject):
    """
    Генерирует подсказку - первый шаг решения задачи
    """
    import logging
    import hashlib
    from django.core.cache import cache
    
    logger = logging.getLogger(__name__)
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        logger.warning("Gemini API key not configured")
        return "⚠️ API ключ Gemini не настроен. Добавьте GEMINI_API_KEY в файл .env"
    
    # Кэширование
    cache_key = hashlib.md5(f"hint_{task_question}_{task_subject}".encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Returning cached hint for {task_subject}")
        return cached
    
    try:
        logger.info(f"Generating hint for subject: {task_subject}")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""Ты - опытный преподаватель по предмету "{task_subject}".

Задача ученика: {task_question}

Дай ТОЛЬКО первый шаг решения этой задачи. Не решай полностью, а подскажи:
- С чего начать
- Какую формулу или метод использовать
- На что обратить внимание

Ответ должен быть кратким (2-3 предложения) и на русском языке."""

        response = model.generate_content(prompt)
        result = response.text
        
        cache.set(cache_key, result, 86400)
        logger.info("Hint generated successfully")
        return result
    
    except Exception as e:
        logger.error(f"Error generating hint: {e}", exc_info=True)
        return f"⚠️ Ошибка при генерации подсказки. Попробуйте позже."


def get_ai_response(user_message, task_question, task_subject):
    """
    Отвечает на произвольный вопрос пользователя о задаче
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        logger.warning("Gemini API key not configured")
        return "⚠️ API ключ Gemini не настроен. Добавьте GEMINI_API_KEY в файл .env"
    
    try:
        logger.info(f"Processing AI question for subject: {task_subject}")
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""Ты - дружелюбный ИИ-помощник для подготовки к ЕГЭ по предмету "{task_subject}".

Текущая задача: {task_question}

Вопрос ученика: {user_message}

Ответь на вопрос ученика:
- Будь дружелюбным и поддерживающим
- Объясняй понятно, как хороший учитель
- Не давай прямой ответ, а направляй к решению
- Используй примеры если нужно
- Пиши на русском языке

Твой ответ:"""

        response = model.generate_content(prompt)
        logger.info("AI response generated successfully")
        return response.text
    
    except Exception as e:
        logger.error(f"Error generating AI response: {e}", exc_info=True)
        return f"⚠️ Ошибка при генерации ответа. Попробуйте позже."
