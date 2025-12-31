import os
import google.generativeai as genai
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY and GEMINI_API_KEY != 'your-gemini-api-key-here':
    genai.configure(api_key=GEMINI_API_KEY)

def get_theory_lesson(task_question, task_subject):
    """
    Генерирует короткий урок с теорией и примерами для задачи
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        return "⚠️ API ключ Gemini не настроен. Добавьте GEMINI_API_KEY в файл .env"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""Ты - опытный преподаватель по предмету "{task_subject}".

Задача ученика: {task_question}

Создай короткий урок (3-4 абзаца) с теорией по этой задаче:
1. Объясни основную концепцию простым языком
2. Приведи 1-2 примера с решением
3. Дай практический совет как решать такие задачи

Пиши на русском языке, понятно и структурированно."""

        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"Ошибка при генерации теории: {str(e)}"


def get_hint(task_question, task_subject):
    """
    Генерирует подсказку - первый шаг решения задачи
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        return "⚠️ API ключ Gemini не настроен. Добавьте GEMINI_API_KEY в файл .env"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""Ты - опытный преподаватель по предмету "{task_subject}".

Задача ученика: {task_question}

Дай ТОЛЬКО первый шаг решения этой задачи. Не решай полностью, а подскажи:
- С чего начать
- Какую формулу или метод использовать
- На что обратить внимание

Ответ должен быть кратким (2-3 предложения) и на русском языке."""

        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"Ошибка при генерации подсказки: {str(e)}"


def get_ai_response(user_message, task_question, task_subject):
    """
    Отвечает на произвольный вопрос пользователя о задаче
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        return "⚠️ API ключ Gemini не настроен. Добавьте GEMINI_API_KEY в файл .env"
    
    try:
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
        return response.text
    
    except Exception as e:
        return f"Ошибка при генерации ответа: {str(e)}"
