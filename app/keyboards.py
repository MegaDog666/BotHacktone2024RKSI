
from gc import callbacks

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Зарeгистрироваться", callback_data="register")]
], resize_keyboard=True)

apply_info = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Принять", callback_data="apply"), InlineKeyboardButton(text="Отклонить", callback_data="create")]
])

create = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать обёртку", callback_data="create")]
], resize_keyboard=True)