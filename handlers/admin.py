from aiogram import Router, F, types
from aiogram.filters import Command
from keyboards import get_admin_keyboard, get_check_prize_keyboard
from database import Database
from config import PRIZES
import random
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

router = Router()
db = Database()

# Список GIF для проигравших
LOSING_GIFS = [
    ("PUSTOY_SEXTOR", "Пустой сектор"),
    ("OSHIBKA_404", "Ошибка 404"),
    ("POCHTI_NO_NET", "Почти, но нет"),
    ("PRIZ_BYL_RYADOM", "Приз был рядом"),
    ("SHANS_BYL_NO_USHOL", "Шанс был, но ушёл")
]

# Маппинг призов на имена переменных с GIF
PRIZE_TO_GIF = {
    "shopper": "SHOPER",
    "notebook": "BLOKNOT",
    "pen": "RUCHKA",
    "mug": "KRUZHKA",
    "discount_10": "SERTIFIKAT_10"
}

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not await db.is_admin(message.from_user.id):
        msg = await message.answer("У вас нет прав администратора.")
        await asyncio.sleep(3)
        await msg.delete()
        await message.delete()
        return
    
    await message.delete()
    await message.answer(
        "Панель администратора:",
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(F.data == "spin_wheel")
async def spin_wheel(callback: types.CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора.")
        return

    # Очищаем предыдущие результаты
    await db.clear_previous_results()

    # Получаем всех игроков
    players = await db.get_all_players()
    if not players:
        await callback.message.edit_text(
            "Нет зарегистрированных игроков.",
            reply_markup=get_admin_keyboard()
        )
        return

    # Анимация розыгрыша
    spinning_msg = await callback.message.edit_text("🎡 Колесо крутится...")
    for i in range(3):
        await asyncio.sleep(1)
        await spinning_msg.edit_text("🎡 Колесо крутится" + "." * (i + 1))

    # Получаем доступные призы
    available_prizes = await db.get_available_prizes()
    
    # Разделяем игроков по классам
    eleventh_graders = [p for p in players if p["grade"] == "11"]
    other_players = [p for p in players if p["grade"] != "11"]
    
    winners_text = "Победители розыгрыша:\n\n"
    winners_info = []  # Список для хранения информации о победителях
    
    # Сначала распределяем сертификаты среди 11-классников
    if eleventh_graders and "discount_10" in available_prizes:
        discount_prize = available_prizes["discount_10"]
        num_certificates = min(len(eleventh_graders), discount_prize["remaining_quantity"])
        winners_11 = random.sample(eleventh_graders, num_certificates)
        
        # Добавляем информацию о победителях-11-классниках
        for winner in winners_11:
            if await db.add_winner(winner["user_id"], "discount_10", PRIZES["discount_10"]["name"]):
                winners_text += f"👤 {winner['full_name']} (Класс: {winner['grade']}) - {PRIZES['discount_10']['name']}\n"
                winners_info.append({
                    "user_id": winner["user_id"],
                    "full_name": winner["full_name"],
                    "grade": winner["grade"],
                    "prize_type": "discount_10",
                    "prize_name": PRIZES["discount_10"]["name"],
                    "gif_id": os.getenv("SERTIFIKAT_10")
                })

    # Распределяем остальные призы среди всех участников
    remaining_players = other_players + [p for p in eleventh_graders if not await db.get_winner_prize(p["user_id"])]
    if remaining_players:
        other_prize_types = [pt for pt in available_prizes.keys() if pt != "discount_10"]
        if other_prize_types:
            random.shuffle(remaining_players)
            random.shuffle(other_prize_types)
            
            for player in remaining_players:
                won_prize = False
                for prize_type in other_prize_types:
                    if await db.add_winner(player["user_id"], prize_type, PRIZES[prize_type]["name"]):
                        winners_text += f"👤 {player['full_name']} (Класс: {player['grade']}) - {PRIZES[prize_type]['name']}\n"
                        winners_info.append({
                            "user_id": player["user_id"],
                            "full_name": player["full_name"],
                            "grade": player["grade"],
                            "prize_type": prize_type,
                            "prize_name": PRIZES[prize_type]["name"],
                            "gif_id": os.getenv(PRIZE_TO_GIF.get(prize_type, ""))
                        })
                        won_prize = True
                        break
                
                # Если игрок не выиграл приз, добавляем его в список с случайным GIF проигрыша
                if not won_prize:
                    random_gif = random.choice(LOSING_GIFS)
                    winners_info.append({
                        "user_id": player["user_id"],
                        "full_name": player["full_name"],
                        "grade": player["grade"],
                        "prize_type": "no_prize",
                        "prize_name": random_gif[1],
                        "gif_id": os.getenv(random_gif[0])
                    })

    # Добавляем статистику по оставшимся призам
    prizes_status = await db.get_prizes_status()
    winners_text += "\n📊 Остаток призов:\n"
    for prize in prizes_status:
        winners_text += f"{prize['prize_name']}: {prize['remaining_quantity']}/{prize['total_quantity']}\n"

    await callback.message.edit_text(
        winners_text,
        reply_markup=get_admin_keyboard()
    )

    # Отправляем GIF-анимации всем игрокам
    for winner in winners_info:
        try:
            if winner["gif_id"]:
                await callback.bot.send_animation(
                    winner["user_id"],
                    animation=winner["gif_id"],
                    caption="🎉 Розыгрыш призов!"
                )
        except Exception as e:
            print(f"Не удалось отправить GIF пользователю {winner['user_id']}: {e}")

    # Ждем 1 секунд
    await asyncio.sleep(1)

    # Отправляем текстовые сообщения всем игрокам
    for winner in winners_info:
        try:
            message_text = "🎉 Результаты розыгрыша:\n\n"
            if winner["prize_type"] == "no_prize":
                message_text += "К сожалению, в этот раз вам не повезло. Попробуйте в следующий раз! 🍀"
            else:
                message_text += f"Поздравляем! Вы выиграли: {winner['prize_name']} 🎁"
            message_text += "\n\nСпасибо за участие! 🎡"
            
            await callback.bot.send_message(
                winner["user_id"],
                message_text
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {winner['user_id']}: {e}")

@router.callback_query(F.data == "winners_list")
async def show_winners(callback: types.CallbackQuery):
    if not await db.is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав администратора.")
        return

    winners = await db.get_all_winners()
    if not winners:
        await callback.message.edit_text(
            "Список победителей пуст.",
            reply_markup=get_admin_keyboard()
        )
        return

    winners_text = "Список всех победителей:\n\n"
    for winner in winners:
        winners_text += (
            f"👤 {winner['full_name']} (Класс: {winner['grade']})\n"
            f"🎁 Приз: {winner['prize_name']}\n"
            f"📅 Дата: {winner['win_date']}\n\n"
        )

    # Добавляем статистику по призам
    prizes_status = await db.get_prizes_status()
    winners_text += "\n📊 Статистика призов:\n"
    for prize in prizes_status:
        winners_text += f"{prize['prize_name']}: {prize['remaining_quantity']}/{prize['total_quantity']}\n"

    await callback.message.edit_text(
        winners_text,
        reply_markup=get_admin_keyboard()
    )

@router.message(F.animation)
async def get_gif_file_id(message: types.Message):
    if not await db.is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    
    file_id = message.animation.file_id
    await message.answer(f"File ID вашего GIF:\n\n`{file_id}`", parse_mode="Markdown") 