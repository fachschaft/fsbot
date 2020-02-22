from typing import Any, Callable, List

import pytest
from asynctest import CoroutineMock, MagicMock, patch

import fsbot.utils.meals as meals

from tests.utils import patch_module

MEAL_DATA = [
    ("day 1", [{"meals": ["Kichererbsenpolenta"]}, {"meals": ["Schweinesteak"]}]),
    ("day 2", [{"meals": ["Eieromelette"]}]),
    ("day 3", [{"meals": ["Merlanfilet paniert"]}]),
]


def setup_module() -> None:
    mock_bot_config = MagicMock()
    mock_bot_config.MENSA_CACHE_URL = 'https://www.mensa_dummy.de/api'
    patch_module(meals, {'bot_config': mock_bot_config})


def mock_get_meals(data: List[Any]) -> Callable[[str], MagicMock]:
    def _mock(url: str) -> MagicMock:
        res = MagicMock()
        num_meals = int(url.split('/')[-1])
        res.__aenter__.return_value.json = CoroutineMock(
            return_value={d[0]: d[1] for d in data[0:num_meals] if d is not None})
        return res
    return _mock


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_empty_result(mock_get: MagicMock) -> None:
    mock_get.return_value.__aenter__.return_value.json = CoroutineMock(return_value={})

    result = await meals.get_food(0, 1)
    assert 'No meals' in result


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_today(mock_get: MagicMock) -> None:
    mock_get.side_effect = mock_get_meals(MEAL_DATA)

    result = await meals.get_food(0, 1)
    assert 'day 1' in result
    assert 'Kichererbsenpolenta' in result


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_tomorrow(mock_get: MagicMock) -> None:
    mock_get.side_effect = mock_get_meals(MEAL_DATA)

    result = await meals.get_food(1, 1)
    assert 'day 1' not in result
    assert 'day 2' in result
    assert 'Eieromelette' in result


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_next_two_days(mock_get: MagicMock) -> None:
    mock_get.side_effect = mock_get_meals(MEAL_DATA)

    result = await meals.get_food(0, 2)
    assert 'day 1' in result
    assert 'Kichererbsenpolenta' in result
    assert 'day 2' in result
    assert 'Eieromelette' in result


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_next_week(mock_get: MagicMock) -> None:
    """If there is no meal on a day (e.g weekend), then there will be no result for that day
    This means the result data is shorter than the requested size (but we don't know which data
    are missing)

    eg. on friday request 3 days -> result = { friday }
    eg. on sunday requiest 3 days -> result = { monday, tuesday }

    Scenario in this test:
    its saturday and the meal for monday is requested
    """
    mock_get.side_effect = mock_get_meals([None, None, *MEAL_DATA])

    result = await meals.get_food(2, 1)
    assert 'day 1' in result
    assert 'Kichererbsenpolenta' in result
