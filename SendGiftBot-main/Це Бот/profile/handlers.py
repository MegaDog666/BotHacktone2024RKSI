from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import profile.keyboards as kb
import json
from db import create_pool
from gpt import answer

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
    cuisine = message.text
    await state.update_data(cuisine=cuisine)
    await message.answer("Отлично! 🎉 Теперь укажи свои интересы (например, искусство, туризм, спорт, еда и т.д.) 🌟")
    await state.set_state(PreferencesForm.interests)

@router.message(PreferencesForm.interests)
async def process_interests(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, подождите несколько секунд! Производится анализ введённых данных 🤔")
    interests = message.text
    data = await state.get_data()
    promo_cuisine = "Ты — мощный инструмент для анализа и коррекции текста. Твоя задача — проверить список кухонь, введённых пользователем через запятую или же, если введён 1 запрос, то его, на соответствие реальным видам кухонь из разных народов. Пример ответа получаемого (например, Китайская, Итальянская, Русская, Испанская и т.д.). Ты должен работать, только с данными ввдёными пользователями, ничего от себя добавлять нельзя! Если пользователь допустил ошибку в названии кухни или ввёл несуществующий вид, ты должен исправить её, указав правильное название. Если пользователь ввёл совершенно несвязный или бессмысленный текст, ты должен удалить такие элементы из списка. Если список пуст, пиши \"NoneObject\", пиши только NoneObject и ничего лишнего, а так же пиши NoneObject, если введённое значение н подходит не под 1 из типов. В ответ пиши только готовый список в строчку через запятую, без ничего лишнего!!! Никогда не пиши ничего кроме данных вариантов!!!!!!!"
    cuisine = answer(data["cuisine"], promo_cuisine)
    cuisine_mass = cuisine.split(",")
    cuisine_out = ", ".join([i.title() for i in cuisine_mass])
    promo_interests = "Ты — мощный инструмент для анализа и коррекции текста. Твоя задача — проверить список интересов или же, если введён 1 запрос, то его, введённых пользователем через запятую, на соответствие реальным интересам (например, спорт, музыка, кино, книги, технологии, еда и т.д.). Ты должен работать, только с данными ввдёными пользователями, ничего от себя добавлять нельзя! Если пользователь допустил ошибку в названии интереса или ввёл несуществующий вид, ты должен исправить её, указав правильное название. Если пользователь ввёл совершенно несвязный или бессмысленный текст, ты должен удалить такие элементы из списка. Если список пуст, пиши \"NoneObject\", пиши только NoneObject и ничего лишнего, а так же пиши NoneObject, если введённое значение н подходит не под 1 из типов. В ответ пиши только готовый список в строчку через запятую, без ничего лишнего!!! Никогда не пиши ничего кроме данных вариантов!!!!!!!"
    interests = answer(interests, promo_interests)
    if str(cuisine) == "NoneObject":
        await message.answer("Ошибка! Вы не ввели не одного подходящего значения, попробуйте ещё раз!\n"
                             "Введите понравившся вам кухни.\n"
                             "(например, итальянская, китайская, русская и т.д.) 🍽️")
        await state.set_state(PreferencesForm.cuisine)
    elif str(interests) == "NoneObject":
        await message.answer("Ошибка! Вы не ввели не одного подходящего значения, попробуйте ещё раз!\n"
                             "Введите понравившся вам интересы.\n"
                             "(например, искусство, туризм, спорт, еда и т.д.) ️")
        await state.set_state(PreferencesForm.interests)
    else:
        interests_mass = interests.split(",")
        await state.update_data(interests=interests)
        user_id = message.from_user.id
        username = message.from_user.username
        await state.update_data(user_id=user_id)
        await state.update_data(username=username)
        interests_out = ", ".join([i.title() for i in interests_mass])
        await message.answer(f"📋 Проверьте, пожалуйста, правильность данных:\n\n"
                f"🎯 Предпочтения по еде: {cuisine_out}\n"
                f"🌟 Предпочтения по интересам: {interests_out}\n"
                f"Всё верно? 🤔", reply_markup=kb.apply_right)

@router.message(Command("edit"))
async def edit_profile(message: Message):
    pool = await create_pool()
    async with pool.acquire() as connection:
        exists = await connection.fetchrow("SELECT * FROM users WHERE user_id = $1", message.from_user.id)
        if exists:
            preferences = await connection.fetchrow("SELECT preferences FROM users WHERE user_id = $1;", message.from_user.id)
            preferences = json.loads(preferences['preferences'])
            cuisine_out = ", ".join([i.title() for i in preferences["cuisine"].split(",")])
            interests_out = ", ".join([i.title() for i in preferences["interests"].split(",")])
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
    await message.answer("Пожалуйста, подождите несколько секунд! Производится анализ введённых данных 🤔")
    cuisine = message.text
    promo_cuisine = "Ты — мощный инструмент для анализа и коррекции текста. Твоя задача — проверить список кухонь, введённых пользователем через запятую или же, если введён 1 запрос, то его, на соответствие реальным видам кухонь из разных народов. Пример ответа получаемого (например, Китайская, Итальянская, Русская, Испанская и т.д.). Ты должен работать, только с данными ввдёными пользователями, ничего от себя добавлять нельзя! Если пользователь допустил ошибку в названии кухни или ввёл несуществующий вид, ты должен исправить её, указав правильное название. Если пользователь ввёл совершенно несвязный или бессмысленный текст, ты должен удалить такие элементы из списка. Если список пуст, пиши \"NoneObject\", пиши только NoneObject и ничего лишнего, а так же пиши NoneObject, если введённое значение н подходит не под 1 из типов. В ответ пиши только готовый список в строчку через запятую, без ничего лишнего!!! Никогда не пиши ничего кроме данных вариантов!!!!!!!"
    cuisine = answer(cuisine, promo_cuisine)
    if str(cuisine) == "NoneObject":
        await message.answer("Ошибка! Вы не ввели не одного подходящего значения, попробуйте ещё раз!\n"
                             "Введите понравившся вам кухни.\n"
                             "(например, итальянская, китайская, русская и т.д.) 🍽️")
        await state.set_state(PreferencesFormEdit.cuisine_edit)
    else:
        cuisine_mass = cuisine.split(",")
        cuisine_out = ", ".join([i.title() for i in cuisine_mass])
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
    await message.answer("Пожалуйста, подождите несколько секунд! Производится анализ введённых данных 🤔")
    interests = message.text
    promo_interests = "Ты — мощный инструмент для анализа и коррекции текста. Твоя задача — проверить список интересов или же, если введён 1 запрос, то его, введённых пользователем через запятую, на соответствие реальным интересам (например, спорт, музыка, кино, книги, технологии, еда и т.д.). Ты должен работать, только с данными ввдёными пользователями, ничего от себя добавлять нельзя! Если пользователь допустил ошибку в названии интереса или ввёл несуществующий вид, ты должен исправить её, указав правильное название. Если пользователь ввёл совершенно несвязный или бессмысленный текст, ты должен удалить такие элементы из списка. Если список пуст, пиши \"NoneObject\", пиши только NoneObject и ничего лишнего, а так же пиши NoneObject, если введённое значение н подходит не под 1 из типов. В ответ пиши только готовый список в строчку через запятую, без ничего лишнего!!! Никогда не пиши ничего кроме данных вариантов!!!!!!!"
    interests = answer(interests, promo_interests)
    if str(interests) == "NoneObject":
        await message.answer("Ошибка! Вы не ввели не одного подходящего значения, попробуйте ещё раз!\n"
                             "Введите понравившся вам интересы.\n"
                             "(например, искусство, туризм, спорт, еда и т.д.) ️")
        await state.set_state(PreferencesFormEdit.interests_edit)
    else:
        interests_mass = interests.split(",")
        interests_out = ", ".join([i.title() for i in interests_mass])
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
        exists = await connection.fetchrow("SELECT * FROM users WHERE user_id = $1", data["user_id"])
        if not exists:
            await connection.execute("INSERT INTO users (user_id, username, preferences) VALUES ($1, $2, $3)", data["user_id"], data["username"], json.dumps(preferences))
            await callback.message.answer("Спасибо! Твои предпочтения сохранены.", reply_markup=kb.start)
            await state.clear()
        else:
            await callback.message.answer("Вы уже имеете аккаунт!")
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
            cuisine_out = ", ".join([i.title() for i in cuisine.split(",")])
            interests_out = ", ".join([i.title() for i in interests.split(",")])
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
