from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from app.states import PreferencesForm, RateForm, pointForm
import app.keyboards as kb
import json

from app.utils import search_by_cuisine, search_by_interests
from config import API_KEY_2GIS
from db.db import create_pool, get_user_preferences_or_notify

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
    await message.answer(
        f"Привет {message.from_user.first_name}!👋 Рады видеть тебя\nв нашем боте о Ростове-на-Дону! 🌆✨\n"
        f"Ты — турист или местный житель? В любом случае, мы поможем тебе открыть город заново\n"
        f"или узнать что-то новое! 🚶‍♂️🚶‍♀️"
        f"\nПривет! Давай настроим твои предпочтения. Какие типы кухни тебе нравятся? (например, итальянская, японская)")
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
            await connection.execute("UPDATE users SET preferences = $1 WHERE user_id = $2", json.dumps(preferences),
                                     user_id)
        else:
            # Создаем нового пользователя
            await connection.execute("INSERT INTO users (user_id, username, preferences) VALUES ($1, $2, $3)", user_id,
                                     message.from_user.username, json.dumps(preferences))
    await message.answer("Спасибо! Твои предпочтения сохранены.", reply_markup=kb.start)


@router.callback_query(F.data == "On_the_way")
async def On_the_way(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(id=callback.from_user.id)
    data = await state.get_data()
    await callback.message.answer(f"Отлично!🌟 Чем вам помочь?\n"
                                  f"Хотите посетить достопримечательности,\n"
                                  f"вкусно поесть 🍽️ или сходить в торговый центр 🛍️?\n"
                                  f"Перед тем как выбрать, нам нужно ваше местоположение для ближайших мест по вашим предпочтениям", reply_markup=kb.location_keyboard)
    await state.clear()

@router.message(F.location)
async def handle_location(message: Message, state: FSMContext):
    global latitude
    global longitude
    latitude = message.location.latitude
    longitude = message.location.longitude
    await message.answer(f"Ваше местоположение: широта {latitude}, долгота {longitude}."
                         f"\nВыберите что бы вы хотели:", reply_markup=kb.apply_info)
    await state.update_data(latitude=latitude, longitude=longitude)
    await state.set_state(pointForm.waiting_for_location)

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
        await connection.execute("INSERT INTO ratings (user_id, place_name, rating) VALUES ($1, $2, $3)", user_id,
                                 place, rating)
    await message.answer(f"Место '{place}' оценено на {rating}.")
    await state.clear()


def generate_recommendations(preferences):
    cuisine = preferences.get("cuisine", [])
    interests = preferences.get("interests", [])
    return f"Рекомендуем: {', '.join(cuisine)} кухня, места по теме {', '.join(interests)}"

####

@router.callback_query(F.data == "eat", pointForm.waiting_for_location)
async def eat_handler(callback: CallbackQuery, state: FSMContext, API_KEY=API_KEY_2GIS):
    data = await state.get_data()
    user_latitude = data.get("latitude")
    user_longitude = data.get("longitude")
    if user_latitude is None or user_longitude is None:
        await callback.answer("Местоположение не определено. Пожалуйста, отправьте локацию.")
        return
    user_id = callback.from_user.id
    preferences = await get_user_preferences_or_notify(user_id, callback, pool)
    if not preferences:
        return

    cuisine = preferences.get("cuisine", [])
    if not cuisine:
        await callback.message.answer("Вы не указали предпочтения по кухням. Попробуйте еще раз.")
        return

    await callback.message.answer(f"Ищем рестораны по вашим предпочтениям: {', '.join(cuisine)}")
    places = await search_by_cuisine(cuisine, API_KEY, user_longitude, user_latitude)

    if places:
        await callback.message.answer("Найденные рестораны:")
        for place in places[:5]:  # Показываем первые 5 ресторанов
            name = place.get("name", "Неизвестный ресторан")
            address = place.get('address_name', "Адрес не указан")
            rating = place.get("rating", "Нет рейтинга")  # Используем функцию для получения рейтинга
            latitude = place.get("latitude")
            longitude = place.get("longitude")
            await callback.message.answer(f"{name}\nАдрес: {address}\nРейтинг: {rating}")
            await callback.message.answer("Вот построенный маршрут:")

            # Отправляем место с картой
            await callback.message.answer_venue(
                title=name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                user_latitude=user_latitude,
                user_longitude=user_longitude
            )
    else:
        await callback.message.answer("К сожалению, по вашему запросу ничего не найдено.")

@router.callback_query(F.data == "visit", pointForm.waiting_for_location)
async def visit_handler(callback: CallbackQuery, state: FSMContext, API_KEY=API_KEY_2GIS):
    global interests
    data = await state.get_data()
    user_latitude = data.get("latitude")
    user_longitude = data.get("longitude")
    if user_latitude is None or user_longitude is None:
        await callback.answer("Местоположение не определено. Пожалуйста, отправьте локацию.")
        return
    user_id = callback.from_user.id
    preferences = await get_user_preferences_or_notify(user_id, callback, pool)
    if preferences:
        interests = preferences.get("interests", [])
        await callback.message.answer(f"Ищем достопримечательности по вашим предпочтениям: {', '.join(interests)}")
    else:
        await callback.message.answer("Сначала укажите свои предпочтения с помощью команды /start.")

    places = await search_by_interests(interests, API_KEY, user_longitude, user_latitude)

    if places:
        await callback.message.answer("Найденные места:")
        for place in places[:5]:  # Показываем первые 5 мест
            name = place.get("name", "Неизвестное место")
            address = place.get('address_name', "Адрес не указан")
            rating = place.get("rating", "Нет рейтинга")  # Используем функцию для получения рейтинга
            latitude = place.get("latitude")
            longitude = place.get("longitude")
            await callback.message.answer(f"{name}\nАдрес: {address}\nРейтинг: {rating}")

            await callback.message.answer("Вот построенный маршрут:")

            # Отправляем место с картой
            await callback.message.answer_venue(
                title=name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                user_latitude=user_latitude,
                user_longitude=user_longitude
            )
    else:
        await callback.message.answer("К сожалению, по вашему запросу ничего не найдено.")
