import time
import typing

import echoroboticsapi
import pytest
import typing
import itertools
from unittest.mock import patch, MagicMock

ALL_MODES = list(typing.get_args(echoroboticsapi.Mode))
ALL_STATUSES = list(typing.get_args(echoroboticsapi.Status))


@pytest.fixture
def robot_id() -> echoroboticsapi.RobotId:
    yield "test_robot_id"


@pytest.fixture
def smart_mode(robot_id) -> echoroboticsapi.SmartMode:
    sm = echoroboticsapi.SmartMode(robot_id=robot_id)
    yield sm


def test_unknown(smart_mode: echoroboticsapi.SmartMode):
    assert smart_mode.get_robot_mode() is None


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ALL_MODES)
async def test_mode_set(
    smart_mode: echoroboticsapi.SmartMode, mode: echoroboticsapi.Mode
):
    await smart_mode.notify_mode_set(mode)
    assert smart_mode.get_robot_mode() == mode


# if status doesn't change after a command, smart_mode should return to these modes
RETURN_TO_MODES: dict[echoroboticsapi.Status, echoroboticsapi.Mode] = {
    "Idle": "chargeAndStay",
    "Work": "work",
    "LeaveStation": "work",
}


@pytest.mark.asyncio
@pytest.mark.parametrize("laststatus, mode", itertools.product(ALL_STATUSES, ALL_MODES))
async def test_laststatus_then_mode(smart_mode, laststatus, mode):
    with patch("time.time", MagicMock(return_value=time.time())) as mock:
        await smart_mode.notify_laststatuses_received(laststatus)
        await smart_mode.notify_mode_set(mode)
        assert smart_mode.get_robot_mode() == mode

        # simulate status hasn't changed yet
        mock.return_value += 1
        await smart_mode.notify_laststatuses_received(laststatus)
        assert smart_mode.get_robot_mode() == mode

        # simulate status doesn't change for long time

        mock.return_value += 120
        await smart_mode.notify_laststatuses_received(laststatus)
        assert smart_mode.get_robot_mode() == RETURN_TO_MODES.get(laststatus, mode)
