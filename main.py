from aiogram import Bot, Dispatcher

from info import TOKEN
from app.handlers import router

bot = Bot(token=TOKEN)

dp = Dispatcher()
dp.include_router(router)

dp.run_polling(bot)

