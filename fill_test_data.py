import asyncio
import random
import aiosqlite
from database import Database

async def fill_test_data():
    db = Database()
    
    # Создаем таблицы, если их нет (не удаляя существующие данные)
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                grade TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.commit()
    
    # Список классов
    grades = ["9", "10", "11"]
    
    # Список имен и фамилий для генерации
    first_names = ["Александр", "Михаил", "Иван", "Дмитрий", "Артем", "Максим", "Даниил", "Марк", "Лев", "Матвей",
                  "София", "Анна", "Мария", "Алиса", "Виктория", "Полина", "Ева", "Елизавета", "Софья", "Александра"]
    
    last_names = ["Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", "Михайлов", "Новиков", "Федоров",
                  "Иванова", "Смирнова", "Кузнецова", "Попова", "Васильева", "Петрова", "Соколова", "Михайлова", "Новикова", "Федорова"]
    
    # Генерируем 100 пользователей
    for i in range(100):
        user_id = 1000000 + i  # Генерируем уникальные user_id
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        full_name = f"{first_name} {last_name}"
        grade = random.choice(grades)
        
        # Добавляем пользователя в базу
        await db.add_user(user_id, full_name, grade, False)
    
    print("База данных успешно заполнена тестовыми данными!")
    
    # Выводим статистику по классам
    async with aiosqlite.connect(db.db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT grade, COUNT(*) as count FROM users GROUP BY grade ORDER BY grade")
        rows = await cursor.fetchall()
        print("\nСтатистика по классам:")
        for row in rows:
            print(f"{row['grade']} класс: {row['count']} учеников")

if __name__ == "__main__":
    asyncio.run(fill_test_data()) 