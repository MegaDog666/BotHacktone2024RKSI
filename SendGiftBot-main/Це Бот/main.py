from aiogram import Bot, Dispatcher

from info import TOKEN
from other.handlers import router as r1
from profile.handlers import router as r2
from get_map.handlers import router as r3

bot = Bot(token=TOKEN)

dp = Dispatcher()
dp.include_routers(r1, r2, r3)

dp.run_polling(bot)

