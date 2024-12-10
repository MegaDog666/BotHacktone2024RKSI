import asyncpg
from config import DB_CONFIG

async def create_pool():
    return await asyncpg.create_pool(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )