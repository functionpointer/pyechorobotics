from datetime import datetime

import echoroboticsapi
import pytest
import typing
import itertools
from unittest.mock import AsyncMock

from echoroboticsapi import RobotId, LastStatuses

ALL_MODES = list(typing.get_args(echoroboticsapi.Mode))
ALL_STATUSES = list(typing.get_args(echoroboticsapi.Status))


@pytest.fixture
def api(robot_id: RobotId):
    api = echoroboticsapi.Api(websession=None, robot_ids=[robot_id])
    yield api


@pytest.fixture
def smart_fetch(api: echoroboticsapi.Api):
    sf = echoroboticsapi.SmartFetch(api, fetch_history_wait_time=5)
    yield sf


def mock_laststatuses(
    robot_id: RobotId, status: echoroboticsapi.Status
) -> LastStatuses:
    posn = echoroboticsapi.Position(longitude=0, latitude=0, date_time=datetime.now())
    si = echoroboticsapi.StatusInfo(
        robot=robot_id,
        status=status,
        mac_address="asdf",
        date=datetime.now(),
        delta="asdf",
        estimated_battery_level=3,
        position=posn,
        query_time=datetime.now(),
        has_values=True,
        is_online=True,
    )
    ls = echoroboticsapi.LastStatuses(
        query_date=datetime.now(),
        robots=[robot_id],
        statuses_info=[si],
        robot_offline_delay_in_seconds=1500,
    )
    return ls


@pytest.mark.asyncio
@pytest.mark.parametrize("status1, status2", itertools.combinations(ALL_STATUSES, 2))
async def test_schedule_smartfetch(
    robot_id: RobotId,
    api: echoroboticsapi.Api,
    smart_fetch: echoroboticsapi.SmartFetch,
    status1: echoroboticsapi.Status,
    status2: echoroboticsapi.Status,
):
    for status in [status1, status2]:
        expected = mock_laststatuses(robot_id, status)
        api.last_statuses = AsyncMock(return_value=expected)
        received = await smart_fetch.smart_fetch()
        assert received == expected

        if status in {
            "Charge",
            "GoUnloadStation",
            "GoChargeStation",
            "GoStation",
        }:
            assert smart_fetch.fetch_history_times[robot_id] > 0
        else:
            assert smart_fetch.fetch_history_times[robot_id] < 0
