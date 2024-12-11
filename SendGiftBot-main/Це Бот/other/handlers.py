from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import other.keyboards as kb
import json
from db import create_pool, get_user_preferences, get_user_preferences_or_notify
from other.utils import get_event_details, search_events_by_city
from pandas.core.indexes.base import str_t

pool = None

router = Router()

API_KEY_TIMEPAD = "8b2f9b4b3b374b93abc65824161e19023109d10b"

class CategorySelection(StatesGroup):
    waiting_for_categories = State()
    user_ID = State()

CATEGORIES_MAP = {
    "1": "Еда",
    "2": "Иностранные языки",
    "3": "Гражданские проекты",
    "4": "Образование за рубежом",
    "5": "Другие события",
    "6": "Спорт",
    "7": "Выставки",
    "8": "Интеллектуальные игры",
    "9": "Хобби и творчество",
    "10": "Кино",
    "11": "Другие развлечения",
    "12": "Красота и здоровье",
    "13": "Концерты",
    "14": "Искусство и культура",
    "15": "Экскурсии и путешествия",
    "16": "Вечеринки",
    "17": "Для детей",
    "18": "Театры",
    "19": "Бизнес",
    "20": "Психология и самопознание",
    "21": "Наука"
}

@router.message(Command("mailings"))
async def mailings(message: Message, state: FSMContext):
    await message.reply("Хотите ли вы получать расссылку по вашим предпочтениям?", parse_mode="Markdown", reply_markup=kb.mailings)

@router.callback_query(F.data == "mailings_confirm")
async def mailings_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("✔️ *Подписка подтверждена!* ✔️\n"
                                  "Ваша подписка на уведомления успешно активирована. Спасибо за использование нашего сервиса! 🌟", parse_mode="Markdown")

    categories_text = "Выберите категории, которые вас интересуют, указав их номера через запятую.\n\n"
    for key, value in CATEGORIES_MAP.items():
        categories_text += f"{key}. {value}\n"
    await callback.message.reply(categories_text)
    await callback.message.answer("Напишите номера категорий через запятую (например, 1, 3, 5):")
    await state.set_state(CategorySelection.waiting_for_categories)

@router.message(CategorySelection.waiting_for_categories)
async def mailings_get(message: Message, state: FSMContext):
    waiting_for_categories = message.text.split(",")
    for categorie in waiting_for_categories:
        if not int(categorie) >= 1 and int(categorie) <= 21:
            await message.answer("Вы указали неверные значения, попробуйте ещё раз!")
            categories_text = "Выберите категории, которые вас интересуют, указав их номера через запятую.\n\n"
            for key, value in CATEGORIES_MAP.items():
                categories_text += f"{key}. {value}\n"
            await message.reply(categories_text)
            await message.answer("Напишите номера категорий через запятую (например, 1, 3, 5):")
            await state.set_state(CategorySelection.waiting_for_categories)
        else:
            await state.update_data(waiting_for_categories=waiting_for_categories)
            await state.update_data(user_ID=message.from_user.id)
    data = await state.get_data()
    cat = [CATEGORIES_MAP.get(i.strip()) for i in data["waiting_for_categories"]]
    await message.answer(f"Это ваши предпочтения? {cat}", reply_markup=kb.mailings_conf)
    await state.clear()

@router.callback_query(F.data == "mailings_conf_edit")
async def mailings_conf_edit(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Ничего страшного, мы всегда можем начать сначала!", parse_mode="Markdown")
    categories_text = "Выберите категории, которые вас интересуют, указав их номера через запятую.\n\n"
    for key, value in CATEGORIES_MAP.items():
        categories_text += f"{key}. {value}\n"
    await callback.message.reply(categories_text)
    await callback.message.answer("Напишите номера категорий через запятую (например, 1, 3, 5):")
    await state.set_state(CategorySelection.waiting_for_categories)

# Отправлять в бд
@router.callback_query(F.data == "mailings_conf_confirm")
async def mailings_conf_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🔔 *Вы подписались на уведомления!* 🔔\n"
                         "Теперь вы будете получать уведомления о новых событиях, каждые 7 дней, турах и интересных местах. Спасибо за подписку! 😊",
                         reply_markup=kb.mailings_send, parse_mode="Markdown")
    pool = await create_pool()
    data = await state.get_data()
    async with pool.acquire() as connection:
        exists = await connection.fetchrow("SELECT * FROM users WHERE user_id = $1", data["user_ID"])
        if exists:
            preferences = await connection.fetchrow("SELECT preferences_2 FROM users WHERE user_id = $1;", data["user_ID"])

@router.callback_query(F.data == "maling_send")
async def maling_send(callback: CallbackQuery, state: FSMContext, API_KEY=API_KEY_TIMEPAD):


    await callback.answer()
    data = await state.get_data()
    user_latitude = data.get("latitude")
    user_longitude = data.get("longitude")
    if user_latitude is None or user_longitude is None:
        await callback.answer("Местоположение не определено. Пожалуйста, отправьте локацию.")
        return
    user_id = callback.from_user.id
    preferences = await get_user_preferences_or_notify(user_id, callback)
    if not preferences:
        return

    categories = preferences.get("categories")
    if not categories:
        await callback.message.answer("Вы не указали предпочтения по категориям. Попробуйте еще раз.")
        return

    await callback.message.answer(f"Ищем события по вашим предпочтениям 🔄")
    events = await get_event_details(categories, API_KEY_TIMEPAD, user_latitude, user_longitude)

    if events:
        await callback.message.answer("Найденные события:")
        for event in events[:5]:
            name = event.get("name", "Неизвестное событие")
            description = event.get("description_html", "Описание не найдено")
            location = event.get("location", {}).get("city", "Город не указан")
            poster_image = event.get("poster_image", {}).get("default_url", "Изображение отсутствует")
            categories_str = ", ".join([cat.get("name", "") for cat in event.get("categories", [])])
            await callback.message.answer(f"🏬 *Название:* {name}\n📍 *Город:* {location}\n *Описание:* {description if description else 'Описание не найдено'}\n🖼 *Постер:* {poster_image}\n🗂 *Категории:* {categories_str}\n\n")


@router.callback_query(F.data == "mailings_cancel")
async def mailings_cancel(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🚫 *Вы отписались от уведомлений!* 🚫\n"
                                  "Теперь вы больше не будете получать уведомления. Если передумаете, вы всегда можете подписаться снова. 🔄", parse_mode="Markdown")