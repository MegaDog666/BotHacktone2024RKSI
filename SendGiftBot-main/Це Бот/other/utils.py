import aiohttp
import asyncio

async def search_events_by_city(city, api_key):
    """
    Ищет события в указанном городе.
    :param city: Город для поиска событий.
    :param api_key: API-ключ Timepad.
    :return: Список событий.
    """
    url = "https://api.timepad.ru/v1/events"
    params = {
        "limit": 5,
        "sort": "+starts_at",
        "cities": city,
        "access_statuses": "public",
        "fields": "location,description_html,poster_image,categories"
    }
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("values", [])
            else:
                print(f"Ошибка: {response.status}")
                print(await response.text())
                return []

async def get_event_details(event):
    """
    Извлекает детали события.
    :param event: Словарь с данными события.
    :return: Словарь с деталями события.
    """
    name = event.get("name", "Неизвестное событие")
    description = event.get("description_html", "Описание отсутствует")
    location = event.get("location", {}).get("city", "Город не указан")
    poster_image = event.get("poster_image", {}).get("default_url", "Изображение отсутствует")
    categories = ", ".join([cat.get("name", "") for cat in event.get("categories", [])])

    return {
        "name": name,
        "description": description,
        "location": location,
        "poster_image": poster_image,
        "categories": categories
    }
