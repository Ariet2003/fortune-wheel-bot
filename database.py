import aiosqlite
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "fortune_wheel.db"):
        self.db_path = db_path

    async def create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT,
                    grade TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS prizes (
                    prize_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prize_type TEXT,
                    prize_name TEXT,
                    quantity INTEGER
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS winners (
                    winner_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    prize_id INTEGER,
                    win_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (prize_id) REFERENCES prizes (prize_id)
                )
            """)
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
            async with db.execute("SELECT * FROM users WHERE is_admin = FALSE") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def add_winner(self, user_id: int, prize_type: str, prize_name: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO prizes (prize_type, prize_name, quantity) VALUES (?, ?, 1) RETURNING prize_id",
                (prize_type, prize_name)
            )
            prize_id = await db.execute("SELECT last_insert_rowid()")
            prize_id = await prize_id.fetchone()
            
            await db.execute(
                "INSERT INTO winners (user_id, prize_id) VALUES (?, ?)",
                (user_id, prize_id[0])
            )
            await db.commit()

    async def get_winner_prize(self, user_id: int) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT w.*, p.prize_name, p.prize_type
                FROM winners w
                JOIN prizes p ON w.prize_id = p.prize_id
                WHERE w.user_id = ?
                ORDER BY w.win_date DESC
                LIMIT 1
            """
            async with db.execute(query, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_winners(self) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT w.*, u.full_name, u.grade, p.prize_name
                FROM winners w
                JOIN users u ON w.user_id = u.user_id
                JOIN prizes p ON w.prize_id = p.prize_id
                ORDER BY w.win_date DESC
            """
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows] 