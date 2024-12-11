from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


mailings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Конечно!", callback_data="mailings_confirm"), InlineKeyboardButton(text="Отмена", callback_data="mailings_cancel")]
], resize_keyboard=True)

mailings_conf = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Да!", callback_data="mailings_conf_confirm"), InlineKeyboardButton(text="Изменить", callback_data="mailings_conf_edit")]
], resize_keyboard=True)

mailings_send = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Посмотрим текущие мероприятия", callback_data="maling_send")]
], resize_keyboard=True)