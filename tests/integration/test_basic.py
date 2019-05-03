import pytest

import rocketbot.master as master


@pytest.mark.asyncio
async def test_basic_connect(bot: master.Master) -> None:
    async with bot:
        pass
    assert True
