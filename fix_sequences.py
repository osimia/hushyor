#!/usr/bin/env python3
"""
Скрипт для сброса PostgreSQL sequences для таблиц Topic и Task
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hushyor.settings')
django.setup()

from django.db import connection

def reset_sequences():
    """Сбрасывает sequences для Topic и Task"""
    with connection.cursor() as cursor:
        # Сбрасываем sequence для Topic
        cursor.execute("""
            SELECT setval(pg_get_serial_sequence('core_topic', 'id'), 
                   COALESCE((SELECT MAX(id) FROM core_topic), 1), 
                   true);
        """)
        
        # Сбрасываем sequence для Task
        cursor.execute("""
            SELECT setval(pg_get_serial_sequence('core_task', 'id'), 
                   COALESCE((SELECT MAX(id) FROM core_task), 1), 
                   true);
        """)
        
        print("✅ Sequences сброшены успешно!")
        print("   - core_topic sequence обновлен")
        print("   - core_task sequence обновлен")

if __name__ == '__main__':
    reset_sequences()
