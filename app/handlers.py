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
    await message.answer(f"Привет, @{message.from_user.username}! 🎩✨\n"
                         f"Зарегистрируйся и открой для себя мир волшебства с обёртками для подарков. Создавай свои шедевры и дари радость с каждым сюрпризом!\n"
                         f"Давай творить! 🎁🎉", reply_markup=kb.start)


@router.callback_query(F.data == "register")
async def register(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(id=callback.from_user.id)
    data = await state.get_data()
    await callback.message.answer(f"✅ Отлично! Вы успешно зарегистрировались.\n"
                                  f"Ваш ID: {data["id"]}\n"
                  f"Теперь вы можете создавать свои уникальные обёртки для подарков! 🎁🎨", reply_markup=kb.create)
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


