#!/usr/bin/env python3
"""Утилита для вывода списка доступных моделей Gemini и поддерживаемых режимов"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Загружаем переменные окружения из .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY не найден. Добавьте его в .env")
    sys.exit(1)

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as exc:
    print(f"❌ Не удалось создать клиента Gemini: {exc}")
    sys.exit(1)

print("\n📋 Доступные модели Gemini:\n")
print(f"{'Имя модели':50} | Поддерживаемые режимы")
print("-" * 90)

try:
    for model in client.models.list():
        methods = ", ".join(model.supported_generation_methods)
        print(f"{model.name:50} | {methods}")
except Exception as exc:
    print(f"❌ Ошибка при получении списка моделей: {exc}")
    sys.exit(1)

print("\n💡 Установите переменную окружения GEMINI_MODEL перед запуском основного скрипта,")
print("   например: $env:GEMINI_MODEL='gemini-1.5-flash-latest'")
