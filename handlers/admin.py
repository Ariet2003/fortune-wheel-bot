from aiogram import Router, F, types
from aiogram.filters import Command
from keyboards import get_admin_keyboard, get_check_prize_keyboard
from database import Database
from config import PRIZES
import random
import asyncio

router = Router()
db = Database()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not await db.is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    await message.answer(
        "Панель администратора:",
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(F.data == "spin_wheel")
async def spin_wheel(callback: types.CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора.")
        return

    # Получаем всех игроков
    players = await db.get_all_players()
    if not players:
        await callback.message.answer("Нет зарегистрированных игроков.")
        return

    # Создаем список призов
    available_prizes = []
    for prize_type, prize_info in PRIZES.items():
        available_prizes.extend([prize_type] * prize_info["quantity"])

    # Перемешиваем призы
    random.shuffle(available_prizes)
    
    # Выбираем победителей
    winners = random.sample(players, min(len(players), len(available_prizes)))
    
    # Анимация розыгрыша
    spinning_msg = await callback.message.answer("🎡 Колесо крутится...")
    for i in range(3):
        await asyncio.sleep(1)
        await spinning_msg.edit_text("🎡 Колесо крутится" + "." * (i + 1))

    # Распределяем призы
    winners_text = "Победители розыгрыша:\n\n"
    for winner, prize_type in zip(winners, available_prizes):
        prize_name = PRIZES[prize_type]["name"]
        await db.add_winner(winner["user_id"], prize_type, prize_name)
        winners_text += f"👤 {winner['full_name']} (Класс: {winner['grade']}) - {prize_name}\n"

    await spinning_msg.delete()
    await callback.message.answer(winners_text)
    
    # Отправляем уведомления победителям
    for winner in winners:
        try:
            await callback.bot.send_message(
                winner["user_id"],
                "🎉 Поздравляем! Вы выиграли в розыгрыше!\nПроверьте свой приз, нажав кнопку ниже:",
                reply_markup=get_check_prize_keyboard()
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление пользователю {winner['user_id']}: {e}")

@router.callback_query(F.data == "winners_list")
async def show_winners(callback: types.CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора.")
        return

    winners = await db.get_all_winners()
    if not winners:
        await callback.message.answer("Список победителей пуст.")
        return

    winners_text = "Список всех победителей:\n\n"
    for winner in winners:
        winners_text += (
            f"👤 {winner['full_name']} (Класс: {winner['grade']})\n"
            f"🎁 Приз: {winner['prize_name']}\n"
            f"📅 Дата: {winner['win_date']}\n\n"
        )

    await callback.message.answer(winners_text) 