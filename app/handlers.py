from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import app.keyboards as kb
import requests

router = Router()

class Registration(StatesGroup):
    id = State()

class PhotoCreate(StatesGroup):
    photos = State()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(f"Привет {message.from_user.first_name}!👋 Рады видеть тебя\nв нашем боте о Ростове-на-Дону! 🌆✨\n"
                         f"Ты — турист или местный житель? В любом случае, мы поможем тебе открыть город заново\n"
                         f"или узнать что-то новое! 🚶‍♂️🚶‍♀️", reply_markup=kb.start)


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

@router.callback_query(F.data == "create")
async def create(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PhotoCreate.photos)
    await callback.message.answer("Для создания фотографии вам необходимо отправить одно или несколько фото.\n\n📸 Отправьте фотографии:")

@router.message(PhotoCreate.photos, F.photo)
async def photo_import(message: Message, state: FSMContext):
    await state.update_data(photos=message.photo[-1].file_id)
    photo_id = await state.get_data()
    await message.answer_photo(photo=photo_id["photos"], caption=f"Это ваши фотографии?", reply_markup=kb.apply_info)
    await state.clear()

@router.callback_query(F.data == "apply")
async def create(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PhotoCreate.photos)
    await callback.message.answer("Для создания фотографии вам необходимо отправить одно или несколько фото.\n\n📸 Отправьте фотографии:")


