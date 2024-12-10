from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from app.states import PreferencesForm, RateForm
import app.keyboards as kb
from db import create_pool
import json


router = Router()
pool = None

class Registration(StatesGroup):
    id = State()

class PhotoCreate(StatesGroup):
    photos = State()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    global pool
    pool = await create_pool()
    await message.answer(f"Привет {message.from_user.first_name}!👋 Рады видеть тебя\nв нашем боте о Ростове-на-Дону! 🌆✨\n"
                         f"Ты — турист или местный житель? В любом случае, мы поможем тебе открыть город заново\n"
                         f"или узнать что-то новое! 🚶‍♂️🚶‍♀️"
                         f"Привет! Давай настроим твои предпочтения. Какие типы кухни тебе нравятся? (например, итальянская, японская)")
    await state.set_state(PreferencesForm.cuisine)


@router.message(PreferencesForm.cuisine)
async def process_cuisine(message: Message, state: FSMContext):
    user_id = message.from_user.id
    cuisine = message.text.split(", ")
    await state.update_data(cuisine=cuisine)
    await message.answer("Отлично! Теперь укажи свои интересы (например, искусство, туризм)")
    await state.set_state(PreferencesForm.interests)


@router.message(PreferencesForm.interests)
async def process_interests(message: Message, state: FSMContext):
    user_id = message.from_user.id
    interests = message.text.split(", ")
    data = await state.get_data()
    preferences = {
        "cuisine": data["cuisine"],
        "interests": interests
    }
    async with pool.acquire() as connection:
        # Проверяем, существует ли пользователь
        exists = await connection.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if exists:
            # Обновляем предпочтения
            await connection.execute("UPDATE users SET preferences = $1 WHERE user_id = $2", json.dumps(preferences), user_id)
        else:
            # Создаем нового пользователя
            await connection.execute("INSERT INTO users (user_id, username, preferences) VALUES ($1, $2, $3)", user_id, message.from_user.username, json.dumps(preferences))
    await message.answer("Спасибо! Твои предпочтения сохранены.", reply_markup=kb.start)

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

