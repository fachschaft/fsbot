import unittest.mock as mock

import pytest
from asynctest import CoroutineMock, patch

import rocketbot.utils.meals as meals

MEAL_DATA = [
    {"day 1": [{"meals": ["Kichererbsenpolenta"]}, {"meals": ["Schweinesteak"]}]},
    {"day 2": [{"meals": ["Eieromelette"]}]},
    {"day 3": [{"meals": ["Merlanfilet paniert"]}]},
]


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_empty_result(mock_get: mock.MagicMock) -> None:
    mock_get.return_value.__aenter__.return_value.json = CoroutineMock(return_value={})

    result = await meals.get_food(0, 1)
    assert 'No meals' in result


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_today(mock_get: mock.MagicMock) -> None:
    mock_get.return_value.__aenter__.return_value.json = CoroutineMock(return_value={**MEAL_DATA[0]})

    result = await meals.get_food(0, 1)
    assert 'day 1' in result
    assert 'Kichererbsenpolenta' in result


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_tomorrow(mock_get: mock.MagicMock) -> None:
    mock_get.return_value.__aenter__.return_value.json = CoroutineMock(return_value={**MEAL_DATA[0], **MEAL_DATA[1]})

    result = await meals.get_food(1, 1)
    assert 'day 1' not in result
    assert 'day 2' in result
    assert 'Eieromelette' in result


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_food_next_two_days(mock_get: mock.MagicMock) -> None:
    mock_get.return_value.__aenter__.return_value.json = CoroutineMock(return_value={**MEAL_DATA[0], **MEAL_DATA[1]})

    result = await meals.get_food(0, 2)
    assert 'day 1' in result
    assert 'Kichererbsenpolenta' in result
    assert 'day 2' in result
    assert 'Eieromelette' in result
