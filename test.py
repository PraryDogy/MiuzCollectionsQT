import sqlite3
from cfg import Static

# Подключение к базе
conn = sqlite3.connect(Static.app_support_db)
cursor = conn.cursor()

# SQL запрос
query = """
UPDATE thumbs 
SET birth = 0, 
    resol = 'none', 
    coll = 'none';
"""

try:
    cursor.execute(query)
    conn.commit()
    print(f"Обновлено записей: {cursor.rowcount}")
except sqlite3.Error as e:
    print(f"Ошибка базы данных: {e}")
finally:
    conn.close()
