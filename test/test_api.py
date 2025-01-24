import asyncio

import aiohttp
import echoroboticsapi
from aioresponses import aioresponses
import pytest
import pytest_asyncio

from echoroboticsapi import RobotId, LastStatuses

@pytest_asyncio.fixture
async def websession():
    session = aiohttp.ClientSession()
    yield session
@pytest.fixture
def aio_m():
    with aioresponses() as m:
        yield m
@pytest.fixture
def api(robot_id: RobotId, websession):
    api = echoroboticsapi.Api(websession=websession, robot_ids=[robot_id])
    yield api

@pytest.mark.asyncio
async def test_get_config(robot_id: RobotId, api: echoroboticsapi.Api, aio_m):
    mock_json = "{'IsError': True, 'IsInProgress': False, 'Message': 'configurator.messages.robotOffline', 'Data': None, 'Descriptors': None, 'ConfigId': 0, 'ConfigVersionId': 0, 'ConfigDateTime': '0001-01-01T00:00:00', 'ConfigValidated': False}"
    expected_url = f"https://myrobot.echorobotics.com/api/RobotConfig/GetConfig/{robot_id}?reload=False"
    aio_m.get(expected_url, payload=mock_json)

    resp = await api.get_config(reload=False, robot_id=robot_id)

    assert resp
    aio_m.assert_called_once_with(expected_url, method="GET")