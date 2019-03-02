import datetime

import pytest

import rocketbot.models as m


@pytest.fixture
def message() -> m.Message:
    return m.Message(
        _id='id',
        _updatedAt=datetime.datetime.now().isoformat(),
        rid='rid',
        msg='',
        ts=datetime.datetime.now().isoformat(),
        u={'_id': '_id', 'username': 'username', 'name': 'name'}
    )
