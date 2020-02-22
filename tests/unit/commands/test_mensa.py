# from typing import Any, Callable, List

import datetime
import pytest
from asynctest import CoroutineMock, MagicMock
from unittest.mock import call

from tests.utils import patch_module

from rocketbot.models.rcdatetime import RcDatetime
from fsbot.commands import mensa


def setup_module() -> None:
    fsbot_mock = MagicMock()
    fsbot_mock.utils = MagicMock()
    fsbot_mock.utils.meals = MagicMock()
    fsbot_mock.utils.meals.get_food = CoroutineMock(return_value=None)
    patch_module(
        mensa,
        {
            'ftfbroker.producer.rocketchat_mensa': MagicMock(),
            'fsbot.utils.meals': fsbot_mock,
        })


def get_pollmanger(poll: MagicMock) -> MagicMock:
    pollmanager_mock = MagicMock()
    pollmanager_mock.create = CoroutineMock()
    pollmanager_mock.polls.get.return_value = poll
    return pollmanager_mock


def get_poll(days: int) -> MagicMock:
    poll_mock = MagicMock()
    poll_mock.title = 'ETM'
    poll_mock.created_on = RcDatetime(datetime.datetime.now() - datetime.timedelta(days=days))
    poll_mock.add_option = CoroutineMock()
    poll_mock.resend_old_message = CoroutineMock()
    return poll_mock


@pytest.mark.asyncio
async def test_should_create_new_poll_when_no_prev_poll_exists() -> None:
    # Arrange
    pollmanager_mock = MagicMock()
    pollmanager_mock.create = CoroutineMock()
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '', MagicMock())

    # Assert
    pollmanager_mock.create.assert_called_once()


@pytest.mark.asyncio
async def test_should_create_new_poll_when_no_poll_from_today_exists() -> None:
    # Arrange
    pollmanager_mock = get_pollmanger(get_poll(1))
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '', MagicMock())

    # Assert
    pollmanager_mock.create.assert_called_once()


@pytest.mark.asyncio
async def test_should_create_new_poll_with_11_30_for_etm() -> None:
    # Arrange
    pollmanager_mock = get_pollmanger(get_poll(1))
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '', MagicMock())

    # Assert
    actual = pollmanager_mock.create.call_args[0][-1]
    assert actual == ['11:30']


@pytest.mark.asyncio
async def test_should_create_new_poll_with_12_30_for_etlm() -> None:
    # Arrange
    pollmanager_mock = get_pollmanger(get_poll(1))
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etlm', '', MagicMock())

    # Assert
    actual = pollmanager_mock.create.call_args[0][-1]
    assert actual == ['12:30']


@pytest.mark.skip
@pytest.mark.asyncio
async def test_should_send_food_message_for_new_poll() -> None:
    pass


@pytest.mark.asyncio
async def test_should_normalize_poll_options_for_new_poll() -> None:
    # Arrange
    pollmanager_mock = get_pollmanger(get_poll(1))
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '1200', MagicMock())

    # Assert
    actual = pollmanager_mock.create.call_args[0][-1]
    assert actual == ['12:00']


@pytest.mark.asyncio
async def test_should_split_poll_options_for_new_poll() -> None:
    # Arrange
    pollmanager_mock = get_pollmanger(get_poll(1))
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '"12:00" "13:00"', MagicMock())

    # Assert
    actual = pollmanager_mock.create.call_args[0][-1]
    assert actual == ['12:00', '13:00']


@pytest.mark.asyncio
async def test_should_not_create_new_poll_when_one_exits_from_today() -> None:
    # Arrange
    pollmanager_mock = get_pollmanger(get_poll(0))
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '', MagicMock())

    # Assert
    pollmanager_mock.create.assert_not_called()


@pytest.mark.asyncio
async def test_should_add_new_option_to_existing_poll() -> None:
    # Arrange
    poll_mock = get_poll(0)
    pollmanager_mock = get_pollmanger(poll_mock)
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '11:30', MagicMock())

    # Assert
    poll_mock.add_option.assert_called_once()
    actual = poll_mock.add_option.call_args
    expected = call('11:30')
    assert expected == actual


@pytest.mark.skip
@pytest.mark.asyncio
async def test_should_preset_user_for_new_option_for_existing_poll() -> None:
    pass


@pytest.mark.asyncio
async def test_should_normalize_poll_options_for_existing_poll() -> None:
    # Arrange
    poll_mock = get_poll(0)
    pollmanager_mock = get_pollmanger(poll_mock)
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '1200', MagicMock())

    # Assert
    actual = poll_mock.add_option.call_args
    expected = call('12:00')
    assert expected == actual


@pytest.mark.asyncio
async def test_should_split_poll_options_for_existing_poll() -> None:
    # Arrange
    poll_mock = get_poll(0)
    pollmanager_mock = get_pollmanger(poll_mock)
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '"12:00" "13:00"', MagicMock())

    # Assert
    actual = poll_mock.add_option.call_args_list
    expected = [call('12:00'), call('13:00')]
    assert expected == actual


@pytest.mark.asyncio
async def test_should_add_default_time_for_etm() -> None:
    # Arrange
    poll_mock = get_poll(0)
    pollmanager_mock = get_pollmanger(poll_mock)
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etm', '', MagicMock())

    # Assert
    actual = poll_mock.add_option.call_args
    expected = call('11:30')
    assert expected == actual


@pytest.mark.asyncio
async def test_should_add_default_time_for_etlm() -> None:
    # Arrange
    poll_mock = get_poll(0)
    pollmanager_mock = get_pollmanger(poll_mock)
    command = mensa.Etm(pollmanager=pollmanager_mock, master=MagicMock())

    # Act
    await command.handle('etlm', '', MagicMock())

    # Assert
    actual = poll_mock.add_option.call_args
    expected = call('12:30')
    assert expected == actual
