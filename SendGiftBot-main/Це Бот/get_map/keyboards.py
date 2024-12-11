from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="В путь!", callback_data="On_the_way")]
], resize_keyboard=True)

apply_info = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Рекомендация от ChatGPT 🧠", callback_data="randomChatGPT")],
    [InlineKeyboardButton(text="Что посетить?", callback_data="visit"), InlineKeyboardButton(text="Где поесть?", callback_data="eat")]
])

location_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отправить местоположение", request_location=True)]
    ],
    resize_keyboard=True
)