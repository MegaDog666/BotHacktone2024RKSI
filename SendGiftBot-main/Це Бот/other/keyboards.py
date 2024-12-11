from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

create = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать обёртку", callback_data="create")]
], resize_keyboard=True)