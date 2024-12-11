from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from states import PreferencesForm, pointForm
import get_map.keyboards as kb
import json
from get_map.utils import search_by_cuisine, search_by_interests
from config import API_KEY_2GIS
from db import create_pool, get_user_preferences_or_notify
from gpt import answer

router = Router()
pool = None

class pointForm(StatesGroup):
    waiting_for_location = State()

class map_struct(StatesGroup):
    position = State()

@router.callback_query(F.data == "On_the_way")
async def answer_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(f"Пожалуйста введи ваше местоположение", reply_markup=kb.location_keyboard)
    await state.set_state(pointForm.waiting_for_location)

@router.message(F.location, pointForm.waiting_for_location)
async def handle_location(message: Message, state: FSMContext):
    global latitude
    global longitude
    latitude = message.location.latitude
    longitude = message.location.longitude
    await message.answer(f"Ваше местоположение: широта {latitude}, долгота {longitude}."
                         f"\nВыберите что бы вы хотели:", reply_markup=kb.apply_info)
    await state.update_data(latitude=latitude, longitude=longitude)

@router.callback_query(F.data == "randomChatGPT")
async def randomChatGPT(callback: CallbackQuery, state: FSMContext, API_KEY=API_KEY_2GIS):
    await callback.answer()
    await callback.message.answer(f"Подождите некоторое время, СhatGPT выбирает для вас место!")
    data = await state.get_data()
    user_latitude = data.get("latitude")
    user_longitude = data.get("longitude")
    cuisine = answer("", "Сгенерируй запрос на интересное место в городе ростове на дону, это будет как рекомендация от тебя, твой ответ должен выглядить так: (например, еда, исскуство, библиотеки)), твой ответ будет передан в запрос к поисковику на карте, он не должен содерать лишнего, только ключевые слова, на твоё усмотрение, не нужно писать вот запрос, сразу пиши ответ!!!!")
    print(cuisine)
    places = await search_by_cuisine(cuisine, API_KEY, user_longitude, user_latitude)
    for place in places[:1]:
        if place:
            name = place.get("name", "Неизвестный ресторан")
            address = place.get('address_name', "Адрес не указан")
            rating = place.get("rating", "Нет рейтинга")
            latitude = place.get("latitude")
            longitude = place.get("longitude")
            await callback.message.answer(
            f"🏬 *Название:* {name.split(",")[0]}\n📍 *Адрес:* {address}\n⭐ *Рейтинг:* {rating} ⭐\n\n"
            "Вот построенный маршрут:", parse_mode="Markdown")
            await callback.message.answer_venue(
                title=name.split(",")[0],
                address=address,
                latitude=latitude,
                longitude=longitude,
                user_latitude=user_latitude,
                user_longitude=user_longitude
            )
        else:
            await callback.message.answer("К сожалению, по вашему запросу ничего не найдено.")


@router.callback_query(F.data == "eat")
async def eat_handler(callback: CallbackQuery, state: FSMContext, API_KEY=API_KEY_2GIS):
    await callback.answer()
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

    cuisine = preferences.get("cuisine")
    if not cuisine:
        await callback.message.answer("Вы не указали предпочтения по кухням. Попробуйте еще раз.")
        return

    await callback.message.answer(f"Ищем рестораны по вашим предпочтениям 🔄")
    places = await search_by_cuisine(cuisine, API_KEY, user_longitude, user_latitude)

    if places:
        await callback.message.answer("Найденные рестораны:")
        for place in places[:5]:
            name = place.get("name", "Неизвестный ресторан")
            description = place.get("description", "Описание не найдено")
            address = place.get('address_name', "Адрес не указан")
            rating = place.get("rating", "Нет рейтинга")
            if not description:
                description = answer(description, f"То напиши своё описания, используя название, адресс и рейтинг ({name}, {address}, {rating})")
            purpose_name = place.get("purpose_name")
            try:
                name_out = name.split(",")[1] if name.split(",")[1] == purpose_name.lower() else name
            except AttributeError:
                name_out = name
            latitude = place.get("latitude")
            longitude = place.get("longitude")
            await callback.message.answer(f"🏬 *Название:* {name.split(",")[0]}\n📍 *Адрес:* {address}\n *Описание:* {description if description else "Описание не найдено"}\n⭐ *Рейтинг:* {rating} ⭐\n\n"
                                                "Вот построенный маршрут:", parse_mode="Markdown")
            await callback.message.answer_venue(
                title=name_out,
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
        await callback.message.answer(f"Ищем достопримечательности по вашим предпочтениям 🔄")
    else:
        await callback.message.answer("Сначала укажите свои предпочтения с помощью команды /start.")

    places = await search_by_interests(interests, API_KEY, user_longitude, user_latitude)

    if places:
        await callback.message.answer("Подождите, введётся обработка 🔄\n"
                                      "Найденные места:")
        for place in places[:5]:  # Показываем первые 5 мест
            name = place.get("name", "Неизвестное место")
            description = place.get("description", "Описание не найдено")
            address = place.get('address_name', "Адрес не указан")
            rating = place.get("rating", "Нет рейтинга")  # Используем функцию для получения рейтинга
            if not description:
                description = answer(description, f"То напиши своё описания, используя название, адресс и рейтинг ({name}, {address}, {rating})")
            purpose_name = place.get("purpose_name")
            try:
                name_out = name.split(",")[1] if name.split(",")[1] == purpose_name.lower() else name
            except AttributeError:
                name_out = name
            latitude = place.get("latitude")
            longitude = place.get("longitude")
            await callback.message.answer(f"🏬 *Название:* {name_out}\n📍 *Адрес:* {address}\n📅 *Описание:* {description if description else "Описание не найдено"}\n⭐ *Рейтинг:* {rating} ⭐\n\n"
                                                "Вот построенный маршрут:", parse_mode="Markdown")
            await callback.message.answer_venue(
                title=name_out,
                address=address,
                latitude=latitude,
                longitude=longitude,
                user_latitude=user_latitude,
                user_longitude=user_longitude
            )
    else:
        await callback.message.answer("К сожалению, по вашему запросу ничего не найдено.")
