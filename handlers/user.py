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
    last_message_id = State()  # Для хранения ID последнего сообщения

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, является ли пользователь админом
    is_admin = await db.is_admin(message.from_user.id)
    if is_admin:
        msg = await message.answer(
            "Добро пожаловать в панель администратора!",
            reply_markup=get_admin_keyboard()
        )
        await state.update_data(last_message_id=msg.message_id)
        return

    user = await db.get_user(message.from_user.id)
    if user:
        msg = await message.answer(
            "С возвращением! Ожидайте начала розыгрыша.", 
            reply_markup=get_play_keyboard()
        )
        await state.update_data(last_message_id=msg.message_id)
        return

    msg = await message.answer("Добро пожаловать в игру Колесо Фортуны! 🎡\nПожалуйста, введите ваше ФИО:")
    await state.set_state(RegistrationStates.waiting_for_name)
    await state.update_data(last_message_id=msg.message_id)

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    # Удаляем предыдущее сообщение бота
    state_data = await state.get_data()
    try:
        await message.bot.delete_message(
            message.chat.id,
            state_data.get("last_message_id")
        )
    except:
        pass
    
    await message.delete()
    await state.update_data(full_name=message.text)
    msg = await message.answer("Выберите ваш класс:", reply_markup=get_grade_keyboard())
    await state.update_data(last_message_id=msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_grade)

@router.message(RegistrationStates.waiting_for_grade)
async def process_grade(message: types.Message, state: FSMContext):
    if message.text not in ["9", "10", "11"]:
        await message.delete()
        msg = await message.answer("Пожалуйста, выберите класс из предложенных вариантов (9, 10, 11)")
        await state.update_data(last_message_id=msg.message_id)
        return

    # Удаляем предыдущее сообщение бота
    state_data = await state.get_data()
    try:
        await message.bot.delete_message(
            message.chat.id,
            state_data.get("last_message_id")
        )
    except:
        pass

    await message.delete()
    user_data = await state.get_data()
    await db.add_user(
        user_id=message.from_user.id,
        full_name=user_data["full_name"],
        grade=message.text
    )

    # Отправляем приветственное сообщение с готовой картинкой
    msg = await message.answer_photo(
        photo="AgACAgIAAxkBAAIFMWfqgqR8W7mBaZETXrNNf94QRqCvAAJf-DEbFOFQS-irnZf24pu8AQADAgADeAADNgQ",
        caption=f"Добро пожаловать, {user_data['full_name']}!\nРегистрация завершена! Нажмите кнопку 'Играть', чтобы участвовать в розыгрыше.",
        reply_markup=get_play_keyboard()
    )
    await state.update_data(last_message_id=msg.message_id)
    await state.clear()

@router.callback_query(F.data == "play_game")
async def play_game(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption="🎡 Вы участвуете в розыгрыше!\nОжидайте, когда администратор начнет игру...",
        reply_markup=None
    )
    await callback.answer("Вы успешно зарегистрированы в розыгрыше!")

@router.callback_query(F.data == "check_prize")
async def check_prize(callback: types.CallbackQuery):
    prize = await db.get_winner_prize(callback.from_user.id)
    if prize:
        text = f"🎉 Поздравляем!\nВаш выигрыш: {prize['prize_name']}"
    else:
        text = "К сожалению, вы пока ничего не выиграли."

    # Проверяем, есть ли у сообщения caption (если это фото)
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=None
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=None
        )
    await callback.answer()

# @router.message(Command("photo"))
# async def request_photo_handler(message: types.Message):
#     await message.answer("Пожалуйста, отправьте фото, чтобы я мог получить его ID.")
#
# @router.message(F.photo)
# async def photo_handler(message: types.Message):
#     photo_id = message.photo[-1].file_id
#     await message.answer(f"ID вашей картинки: {photo_id}")