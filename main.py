import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import load_config
from handlers import admin, user
from database import Database

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Функция конфигурации и запуска бота
async def main():
    # Загружаем конфигурацию
    config = load_config()
    
    # Инициализируем бот и диспетчер
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Инициализируем базу данных
    db = Database()
    await db.create_tables()
    
    # Регистрируем администратора
    await db.add_user(
        user_id=config.admin_id,
        full_name="Администратор",
        grade="Admin",
        is_admin=True
    )
    
    # Регистрируем роутеры
    dp.include_router(admin.router)
    dp.include_router(user.router)
    
    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 