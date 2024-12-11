import ssl
import aiohttp
import certifi


async def search_places(query, api_key, longitude, latitude):
    """
    Поиск мест через API 2GIS.
    :param query: Запрос для поиска.
    :param api_key: API-токен 2GIS.
    :return: Список найденных мест с рейтингом.
    """
    url = "https://catalog.api.2gis.com/3.0/items"
    params = {
        "q": query,
        "sort_point": f"{longitude},{latitude}",
        "radius": 5000,
        "key": api_key,
        "locale": "ru_RU",
        "fields": "items.reviews,items.point",  # Добавляем рейтинг
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, ssl=ssl_context) as response:
            if response.status == 200:
                data = await response.json()
                print(f"Ответ API: {data}")
                return data.get("result", {}).get("items", [])
            else:
                print(f"Ошибка API 2GIS: {response.status}")
                return []

def get_rating(reviews):
    """
    Извлекает рейтинг из ответа API.
    :param reviews: Объект с отзывами и рейтингами.
    :return: Рейтинг или "Нет рейтинга".
    """
    # Приоритетный рейтинг
    rating = reviews.get("general_rating")
    if rating is None:
        # Запасной рейтинг
        rating = reviews.get("org_rating")
    if rating is None:
        # Если рейтинг вообще отсутствует
        rating = "Нет рейтинга"
    return rating
async def search_by_interests(interests, api_key, longitude, latitude):
    """
    Ищет места по интересам.
    :param interests: Список интересов.
    :param api_key: API-ключ 2GIS.
    :return: Список мест с рейтингами.
    """
    query = " ".join(interests)
    places = await search_places(query, api_key, longitude, latitude)
    results = []
    for place in places:
        name = place.get("name", "Неизвестное место")
        address = place.get("address_name", "Адрес не указан")
        rating = get_rating(reviews=place.get("reviews", {}))
        point = place.get("point", {})
        latitude = point.get("lat")
        longitude = point.get("lon")
        results.append({
            "name": name,
            "address_name": address,
            "rating": rating,
            "latitude": latitude,
            "longitude": longitude
        })

    return results

async def search_by_cuisine(cuisine, api_key, longitude, latitude):
    query = f"рестораны {', '.join(cuisine)} кухня"
    places = await search_places(query, api_key, longitude, latitude)
    results = []
    for place in places:
        name = place.get("name", "Неизвестное место")
        address = place.get("address_name", "Адрес не указан")
        rating = get_rating(reviews=place.get("reviews", {}))
        point = place.get("point", {})
        latitude = point.get("lat")
        longitude = point.get("lon")
        results.append({
            "name": name,
            "address_name": address,
            "rating": rating,
            "latitude": latitude,
            "longitude": longitude
        })

    return results