from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import app.keyboards as kb
import json
from db import create_pool


pool = None

router = Router()

class PreferencesForm(StatesGroup):
    cuisine = State()
    interests = State()
    user_id = State()
    username = State()

class PreferencesFormEdit(StatesGroup):
    cuisine_edit = State()
    interests_edit = State()
    user_id_edit = State()

class RateForm(StatesGroup):
    place = State()
    rating = State()

class SearchForm(StatesGroup):
    query = State()

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    global pool
    pool = await create_pool()
    async with pool.acquire() as connection:
        # Проверяем, существует ли пользователь
        exists = await connection.fetchrow("SELECT * FROM users WHERE user_id = $1", message.from_user.id)
        if exists:
            preferences = await connection.fetchrow("SELECT preferences FROM users WHERE user_id = $1;", message.from_user.id)
            preferences = json.loads(preferences['preferences'])
            cuisine_out = ", ".join([i.title() for i in preferences["cuisine"]])
            interests_out = ", ".join([i.title() for i in preferences["interests"]])
            await message.reply(
                f"Привет, {message.from_user.username}! 😊\n"
                f"Вот твои текущие настройки:\n\n"
                f"🎯 Предпочтения по еде: {cuisine_out}\n"
                f"🌟 Предпочтения по интересам: {interests_out}\n\n"
                f"Если хочешь изменить их, используй команду /edit."
            )
        else:
            await message.answer(f"Привет, @{message.from_user.username}! 👋\n"
                             f"Рады видеть тебя в нашем гид боте по Ростову-на-Дону! 🌆✨\n"
                             f"Давай настроим твои предпочтения. Какие типы кухни тебе нравятся? 🍽️\n"
                             f"(например, итальянская, японская, русская и т.д.)")
            await state.set_state(PreferencesForm.cuisine)

@router.message(PreferencesForm.cuisine)
async def process_cuisine(message: Message, state: FSMContext):
    cuisine = message.text.split(",")
    await state.update_data(cuisine=cuisine)
    await message.answer("Отлично! 🎉 Теперь укажи свои интересы (например, искусство, туризм, спорт, еда и т.д.) 🌟")
    await state.set_state(PreferencesForm.interests)

@router.message(PreferencesForm.interests)
async def process_interests(message: Message, state: FSMContext):
    interests = message.text.split(",")
    user_id = message.from_user.id
    username = message.from_user.username
    await state.update_data(interests=interests)
    await state.update_data(user_id=user_id)
    await state.update_data(username=username)
    data = await state.get_data()
    cuisine_out = ", ".join([i.title() for i in data["cuisine"]])
    interests_out = ", ".join([i.title() for i in interests])

    await message.answer(f"📋 Проверь, пожалуйста, правильность данных:\n\n"
                f"🎯 Предпочтения по еде: {cuisine_out}\n"
                f"🌟 Предпочтения по интересам: {interests_out}\n"
                f"Всё верно? 🤔", reply_markup=kb.apply_right)

@router.message(Command("edit"))
async def edit_profile(message: Message):
    pool = await create_pool()
    async with pool.acquire() as connection:
        # Проверяем, существует ли пользователь
        exists = await connection.fetchrow("SELECT * FROM users WHERE user_id = $1", message.from_user.id)
        if exists:
            preferences = await connection.fetchrow("SELECT preferences FROM users WHERE user_id = $1;", message.from_user.id)
            preferences = json.loads(preferences['preferences'])
            cuisine_out = ", ".join([i.title() for i in preferences["cuisine"]])
            interests_out = ", ".join([i.title() for i in preferences["interests"]])
            await message.reply(
                f"Привет, {message.from_user.username}! 😊\n"
                f"Вот твои текущие настройки:\n\n"
                f"🎯 Предпочтения по еде: {cuisine_out}\n"
                f"🌟 Предпочтения по интересам: {interests_out}\n\n"
                f"Выберите, что вы хотите изменить:", reply_markup=kb.edit_profile)
        else:
            await message.answer("⚠️ У вас еще нет аккаунта. Пожалуйста, пройдите регистрацию, чтобы создать профиль.\n"
                                 "Нажмите /start, чтобы начать регистрацию.")

@router.callback_query(F.data == "edit_profile_food_preferences")
async def edit_profile_food_preferences(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🍽️ Давай изменим твои предпочтения по еде! Напиши, какие типы кухни тебе нравятся (например, итальянская, японская, русская и т.д.).")
    await state.set_state(PreferencesFormEdit.cuisine_edit)

@router.message(PreferencesFormEdit.cuisine_edit)
async def edit_profile_process_cuisine(message: Message, state: FSMContext):
    cuisine = message.text.split(",")
    cuisine_out = ", ".join([i.title() for i in cuisine])
    await state.update_data(cuisine_edit=cuisine)
    await state.update_data(user_id_edit=message.from_user.id)
    await message.answer("Успешно! 🎉\n"
                         f"Текущие изменение: {cuisine_out}", reply_markup=kb.edit_profile_process_cuisine)

@router.callback_query(F.data == "edit_profile_process_cuisine_apply")
async def edit_profile_cuisine_preferences(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    pool = await create_pool()
    async with pool.acquire() as connection:
        preferences = await connection.fetchrow("SELECT preferences FROM users WHERE user_id = $1;", data["user_id_edit"])
        preferences = json.loads(preferences['preferences'])
        interests = preferences["interests"]
        preferences = {
            "cuisine": data["cuisine_edit"],
            "interests": interests
        }
        await connection.execute("UPDATE users SET preferences = $1 WHERE user_id = $2", json.dumps(preferences), data["user_id_edit"])
    await callback.message.answer("✅ Ваши предпочтения по еде успешно изменены! Используйте комманду /profile, чтобы увидеть текущие предпочтения.")
    await state.clear()

@router.callback_query(F.data == "edit_profile_interest_preferences")
async def edit_profile_interest_preferences(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🎯 Давай изменим твои предпочтения по интересам! Напиши, что тебя интересует (например, туризм, спорт, еда и т.д.).")
    await state.set_state(PreferencesFormEdit.interests_edit)

@router.message(PreferencesFormEdit.interests_edit)
async def edit_profile_process_interests(message: Message, state: FSMContext):
    interests = message.text.split(",")
    interests_out = ", ".join([i.title() for i in interests])
    await state.update_data(interests_edit=interests)
    await state.update_data(user_id_edit=message.from_user.id)
    await message.answer("Успешно! 🎉\n"
                         f"Текущие изменение: {interests_out}", reply_markup=kb.edit_profile_process_interests)


@router.callback_query(F.data == "edit_profile_process_interests_apply")
async def edit_profile_interest_preferences(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    pool = await create_pool()
    async with pool.acquire() as connection:
        preferences = await connection.fetchrow("SELECT preferences FROM users WHERE user_id = $1;", data["user_id_edit"])
        preferences = json.loads(preferences['preferences'])
        cuisine = preferences["cuisine"]
        preferences = {
            "cuisine": cuisine,
            "interests": data["interests_edit"]
        }
        await connection.execute("UPDATE users SET preferences = $1 WHERE user_id = $2", json.dumps(preferences), data["user_id_edit"])
    await callback.message.answer("✅ Ваши предпочтения по интересам успешно изменены! Используйте комманду /profile, чтобы увидеть текущие предпочтения.")
    await state.clear()

@router.callback_query(F.data == "edit_profile_cancel")
async def edit_profile_cancel(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("❌ Отменено. Ты всегда можешь вернуться и изменить данные с помощью команды /edit.")

@router.callback_query(F.data == "yes_apply_right")
async def yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    preferences = {
        "cuisine": data["cuisine"],
        "interests": data["interests"]
    }
    async with pool.acquire() as connection:
        await connection.execute("INSERT INTO users (user_id, username, preferences) VALUES ($1, $2, $3)", data["user_id"], data["username"], json.dumps(preferences))
        await callback.message.answer("Спасибо! Твои предпочтения сохранены.", reply_markup=kb.start)
        await state.clear()

@router.message(Command("profile"))
async def profile(message: Message):
    pool = await create_pool()
    async with pool.acquire() as connection:
        exists = await connection.fetchrow("SELECT * FROM users WHERE user_id = $1", message.from_user.id)
        if exists:
            preferences = await connection.fetchrow("SELECT preferences FROM users WHERE user_id = $1;", message.from_user.id)
            preferences = json.loads(preferences['preferences'])
            cuisine = preferences["cuisine"]
            interests = preferences["interests"]
            cuisine_out = ", ".join([i.title() for i in cuisine])
            interests_out = ", ".join([i.title() for i in interests])
            await message.reply("👤 Ваш профиль:\n\n"
                        f"🍽️ Предпочтения по еде:\n"
                        f"{cuisine_out}\n"
                        f"🎯 Предпочтения по интересам:\n"
                        f"{interests_out}\n\n"
                        f"🔄 Чтобы изменить данные, используйте команду /edit.")
        else:
            await message.answer("⚠️ У вас еще нет аккаунта. Пожалуйста, пройдите регистрацию, чтобы создать профиль.\n"
                                 "Нажмите /start, чтобы начать регистрацию.")

@router.callback_query(F.data == "no_apply_right")
async def no(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PreferencesForm.cuisine)
    await  callback.message.answer("Ничего страшного! Давай настроим твои предпочтения заново. Какие типы кухни тебе нравятся? 🍽️\n"
                                   "(например, итальянская, японская, русская и т.д.)")

@router.callback_query(F.data == "On_the_way")
async def On_the_way(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(id=callback.from_user.id)
    data = await state.get_data()
    await callback.message.answer(f"Отлично!🌟 Чем вам помочь?\n"
                                   f"Хотите посетить достопримечательности,\n"
                                   f"вкусно поесть 🍽️ или сходить в торговый центр 🛍️?\n"
                                   f"Выберите, что вам интересно:", reply_markup=kb.apply_info)
    await state.clear()

####
@router.message(Command("recommendations"))
async def get_recommendations(message: Message):
    user_id = message.from_user.id
    async with pool.acquire() as connection:
        preferences = await connection.fetchrow("SELECT preferences FROM users WHERE user_id = $1", user_id)
        if preferences:
            preferences = json.loads(preferences["preferences"])
            recommendations = generate_recommendations(preferences)
            await message.answer(f"Ваши рекомендации: {recommendations}")
        else:
            await message.answer("Сначала укажите свои предпочтения с помощью команды /start.")

@router.message(Command("rate"))
async def rate_place(message: Message):
    await message.answer("Введите название места:")
    await RateForm.place.set()

@router.message(RateForm.place)
async def process_place(message: Message, state: FSMContext):
    await state.update_data(place=message.text)
    await message.answer("Введите рейтинг (от 1 до 5):")
    await RateForm.rating.set()

@router.message(RateForm.rating)
async def process_rating(message: Message, state: FSMContext):
    user_id = message.from_user.id
    rating = int(message.text)
    data = await state.get_data()
    place = data["place"]
    async with pool.acquire() as connection:
        await connection.execute("INSERT INTO ratings (user_id, place_name, rating) VALUES ($1, $2, $3)", user_id, place, rating)
    await message.answer(f"Место '{place}' оценено на {rating}.")
    await state.clear()


def generate_recommendations(preferences):
    cuisine = preferences.get("cuisine", [])
    interests = preferences.get("interests", [])
    return f"Рекомендуем: {', '.join(cuisine)} кухня, места по теме {', '.join(interests)}"

####