from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import other.keyboards as kb
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