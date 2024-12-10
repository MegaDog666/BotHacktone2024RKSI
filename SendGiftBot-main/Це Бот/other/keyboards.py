from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Поехали", callback_data="On_the_way")]
], resize_keyboard=True)

apply_info = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Что посетить?", callback_data="choice")],
    [InlineKeyboardButton(text="Торговые центры", callback_data="choice"), InlineKeyboardButton(text="Где поесть?", callback_data="choice")]
], resize_keyboard=True)


create = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Создать обёртку", callback_data="create")]
], resize_keyboard=True)