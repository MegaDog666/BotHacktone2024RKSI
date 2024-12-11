import asyncpg
import json
from config import DB_CONFIG

async def create_pool():
    return await asyncpg.create_pool(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )

async def get_user_preferences(user_id, pool):
    pool = await create_pool()
    async with pool.acquire() as connection:
        preferences = await connection.fetchrow("SELECT preferences FROM users WHERE user_id = $1", user_id)
        if preferences:
            # Преобразуем JSON-строку в словарь
            return json.loads(preferences["preferences"])
        else:
            print(f"No preferences found for user {user_id}")
            return None

async def get_user_preferences_or_notify(user_id, callback, pool):
    preferences = await get_user_preferences(user_id, pool)
    if not preferences:
        await callback.message.answer("Сначала укажите свои предпочтения с помощью команды /start.")
    return preferences
