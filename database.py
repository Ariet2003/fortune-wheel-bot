import aiosqlite
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "fortune_wheel.db"):
        self.db_path = db_path

    async def create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Создаем таблицу пользователей, если её нет
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    grade TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Удаляем только таблицы с призами и победителями
            await db.execute("DROP TABLE IF EXISTS winners")
            await db.execute("DROP TABLE IF EXISTS available_prizes")
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS available_prizes (
                    prize_type TEXT PRIMARY KEY,
                    prize_name TEXT,
                    total_quantity INTEGER,
                    remaining_quantity INTEGER
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS winners (
                    winner_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    prize_type TEXT,
                    prize_name TEXT,
                    win_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (prize_type) REFERENCES available_prizes (prize_type)
                )
            """)
            
            # Инициализация призов
            prizes_data = [
                ("discount_10", "Сертификат на скидку 10%", 20),
                ("mug", "Кружка", 5),
                ("notebook", "Блокнот", 5),
                ("pen", "Ручка", 5),
                ("shopper", "Шоппер", 5)
            ]
            
            await db.executemany(
                "INSERT INTO available_prizes (prize_type, prize_name, total_quantity, remaining_quantity) VALUES (?, ?, ?, ?)",
                [(p[0], p[1], p[2], p[2]) for p in prizes_data]
            )
            
            await db.commit()

    async def add_user(self, user_id: int, full_name: str, grade: str, is_admin: bool = False) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (user_id, full_name, grade, is_admin) VALUES (?, ?, ?, ?)",
                (user_id, full_name, grade, is_admin)
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def is_admin(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    async def get_all_players(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE is_admin = FALSE ORDER BY grade DESC") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def clear_previous_results(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            # Очищаем победителей
            await db.execute("DELETE FROM winners")
            # Сбрасываем количество оставшихся призов до максимального
            await db.execute("UPDATE available_prizes SET remaining_quantity = total_quantity")
            await db.commit()

    async def get_available_prizes(self) -> Dict[str, Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM available_prizes WHERE remaining_quantity > 0") as cursor:
                rows = await cursor.fetchall()
                prizes = {}
                for row in rows:
                    prizes[row['prize_type']] = dict(row)
                return prizes

    async def add_winner(self, user_id: int, prize_type: str, prize_name: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем доступность приза
            async with db.execute(
                "SELECT remaining_quantity FROM available_prizes WHERE prize_type = ?",
                (prize_type,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row or row[0] <= 0:
                    return False

            # Уменьшаем количество доступных призов
            await db.execute(
                "UPDATE available_prizes SET remaining_quantity = remaining_quantity - 1 WHERE prize_type = ?",
                (prize_type,)
            )
            
            # Добавляем победителя
            await db.execute(
                "INSERT INTO winners (user_id, prize_type, prize_name) VALUES (?, ?, ?)",
                (user_id, prize_type, prize_name)
            )
            
            await db.commit()
            return True

    async def get_winner_prize(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT *
                FROM winners
                WHERE user_id = ?
                ORDER BY win_date DESC
                LIMIT 1
            """
            async with db.execute(query, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_winners(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT w.*, u.full_name, u.grade
                FROM winners w
                JOIN users u ON w.user_id = u.user_id
                ORDER BY w.win_date DESC
            """
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_prizes_status(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM available_prizes ORDER BY prize_type"
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows] 