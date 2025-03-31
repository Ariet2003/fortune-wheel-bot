from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import get_grade_keyboard, get_play_keyboard, get_check_prize_keyboard, get_admin_keyboard
from database import Database

router = Router()
db = Database()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_grade = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, является ли пользователь админом
    is_admin = await db.is_admin(message.from_user.id)
    if is_admin:
        await message.answer(
            "Добро пожаловать в панель администратора!",
            reply_markup=get_admin_keyboard()
        )
        return

    user = await db.get_user(message.from_user.id)
    if user:
        await message.answer("С возвращением! Ожидайте начала розыгрыша.", 
                           reply_markup=get_play_keyboard())
        return

    await message.answer("Добро пожаловать в игру Колесо Фортуны! 🎡\nПожалуйста, введите ваше ФИО:")
    await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Выберите ваш класс:", reply_markup=get_grade_keyboard())
    await state.set_state(RegistrationStates.waiting_for_grade)

@router.message(RegistrationStates.waiting_for_grade)
async def process_grade(message: types.Message, state: FSMContext):
    if message.text not in ["9", "10", "11"]:
        await message.answer("Пожалуйста, выберите класс из предложенных вариантов (9, 10, 11)")
        return

    user_data = await state.get_data()
    await db.add_user(
        user_id=message.from_user.id,
        full_name=user_data["full_name"],
        grade=message.text
    )

    # Отправляем приветственное сообщение с готовой картинкой
    await message.answer_photo(
        photo="AgACAgIAAxkBAAIFMWfqgqR8W7mBaZETXrNNf94QRqCvAAJf-DEbFOFQS-irnZf24pu8AQADAgADeAADNgQ",
        caption=f"Добро пожаловать, {user_data['full_name']}!\nРегистрация завершена! Ожидайте начала розыгрыша.",
        reply_markup=get_play_keyboard()
    )
    await state.clear()

@router.callback_query(F.data == "check_prize")
async def check_prize(callback: types.CallbackQuery):
    prize = await db.get_winner_prize(callback.from_user.id)
    if prize:
        await callback.message.answer(
            f"Поздравляем! Ваш выигрыш: {prize['prize_name']}"
        )
    else:
        await callback.message.answer("К сожалению, вы пока ничего не выиграли.")
    await callback.answer() 

#Хендлер для обработки команды "/photo"
@router.message(Command("photo"))
async def request_photo_handler(message: types.Message):
    await message.answer("Пожалуйста, отправьте фото, чтобы я мог получить его ID.")


# Хендлер для обработки фото от пользователя
@router.message(F.photo)
async def photo_handler(message: types.Message):
    # Берем фотографию в самом большом разрешении и получаем ее ID
    photo_id = message.photo[-1].file_id
    await message.answer(f"ID вашей картинки: {photo_id}")