from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_grade_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=str(grade)) for grade in [9, 10, 11]]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_play_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🎮 Играть", callback_data="play_game")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🎲 Крутить колесо", callback_data="spin_wheel")],
        [InlineKeyboardButton(text="📊 Список победителей", callback_data="winners_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_check_prize_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🎁 Мой выигрыш", callback_data="check_prize")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 