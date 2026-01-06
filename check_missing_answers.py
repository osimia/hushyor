#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки тестов без ответов
"""

import json

# Читаем ответы
with open('answer_keys.json', 'r', encoding='utf-8') as f:
    answers = json.load(f)

print(f"📊 Всего ответов в answer_keys.json: {len(answers)}")
print(f"📊 ID от 1 до: {max([int(k) for k in answers.keys()])}")

# Проверяем какие ID отсутствуют от 1 до 919
missing_ids = []
for i in range(1, 920):
    if str(i) not in answers:
        missing_ids.append(i)

print(f"\n❌ Тестов БЕЗ ответов (от 1 до 919): {len(missing_ids)}")
print(f"\n📝 Список ID без ответов:")
print(missing_ids)

# Группируем по диапазонам для удобства
if missing_ids:
    print(f"\n📋 Диапазоны ID без ответов:")
    start = missing_ids[0]
    prev = missing_ids[0]
    
    for i in range(1, len(missing_ids)):
        if missing_ids[i] != prev + 1:
            if start == prev:
                print(f"   {start}")
            else:
                print(f"   {start}-{prev}")
            start = missing_ids[i]
        prev = missing_ids[i]
    
    if start == prev:
        print(f"   {start}")
    else:
        print(f"   {start}-{prev}")

print(f"\n✅ Тестов С ответами (от 1 до 919): {919 - len(missing_ids)}")
