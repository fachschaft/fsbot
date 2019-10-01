import aiohttp

import bot_config as c


async def get_food(offset: int, num_meals: int) -> str:
    """Get the food which will be served

    Offset defines the first meal which will be in the result
    offset = 0 -> today
    offset = 1 -> tomorrow

    Num_meals defines the number of meals which will be in the result

    Examles:
    Food for today -> get_food(0, 1)
    Food for the week -> get_food(0, 7)
    Food for tomorrow and the day after -> get_food(1, 2)
    """
    url1 = c.MENSA_CACHE_URL + '/' + str(offset)
    url2 = c.MENSA_CACHE_URL + '/' + str(offset + num_meals)

    async with aiohttp.ClientSession() as session:
        async with session.get(url1) as resp:
            data1 = await resp.json()
        async with session.get(url2) as resp:
            data2 = await resp.json()

    foodmsg = ['```']
    for i, (day, meals) in enumerate(data2.items()):
        if i < len(data1):
            continue
        foodmsg.append(day)
        for j, meal in enumerate(meals):
            foodmsg.append(f'  Meal: {j+1}')
            for line in meal['meals']:
                foodmsg.append(f'    {line}')

    if len(foodmsg) == 1:
        foodmsg.append('No meals received.')
    foodmsg.append('```')

    return '\n'.join(foodmsg)
