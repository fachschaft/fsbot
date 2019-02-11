import json
import urllib.request
import bot_config as c


async def get_food(days=None):
    if days is None:
        days = 1
    url = c.MENSA_CACHE_URL + '/' + str(days)

    with urllib.request.urlopen(url) as url_obj:
        data = json.loads(url_obj.read().decode())

    foodmsg = "```\n"
    for day in data:
        foodmsg += day + "\n"
        for i, meal in enumerate(data[day]):
            foodmsg += "  Meal: " + str(i) + "\n"
            for line in meal['meals']:
                foodmsg += "    " + line + "\n"
    foodmsg += "```\n"

    return foodmsg
