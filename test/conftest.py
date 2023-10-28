import pytest

import echoroboticsapi


@pytest.fixture
def robot_id() -> echoroboticsapi.RobotId:
    yield "test_robot_id"


@pytest.fixture
def smart_mode(robot_id) -> echoroboticsapi.SmartMode:
    sm = echoroboticsapi.SmartMode(robot_id=robot_id)
    yield sm
