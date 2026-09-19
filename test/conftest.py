from typing import Any, Generator

import pytest

import echoroboticsapi


@pytest.fixture
def robot_id() -> echoroboticsapi.RobotId:
    yield "TEST_ROBOT_ID"

@pytest.fixture
def user_email() -> Generator[str, Any, None]:
    yield "user_email"

@pytest.fixture
def user_password() -> Generator[str, Any, None]:
    yield "user_password"

@pytest.fixture
def smart_mode(robot_id) -> echoroboticsapi.SmartMode:
    sm = echoroboticsapi.SmartMode(robot_id=robot_id)
    yield sm
