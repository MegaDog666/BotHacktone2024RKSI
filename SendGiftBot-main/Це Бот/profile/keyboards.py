from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

apply_right = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Да, всё верно!", callback_data="yes_apply_right"), InlineKeyboardButton(text="↩️ Нет, давай начнем заново", callback_data="no_apply_right")]
], resize_keyboard=True)

edit_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🍽️ Предпочтения по еде", callback_data="edit_profile_food_preferences"), InlineKeyboardButton(text="🎯 Предпочтения по интересам", callback_data="edit_profile_interest_preferences")],
    [InlineKeyboardButton(text="❌ Отмена", callback_data="edit_profile_cancel")]
], resize_keyboard=True)

edit_profile_process_cuisine = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подтвердить!", callback_data="edit_profile_process_cuisine_apply"), InlineKeyboardButton(text="❌ Отмена", callback_data="edit_profile_cancel")]
], resize_keyboard=True)

edit_profile_process_interests = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подтвердить!", callback_data="edit_profile_process_interests_apply"), InlineKeyboardButton(text="❌ Отмена", callback_data="edit_profile_cancel")]
], resize_keyboard=True)