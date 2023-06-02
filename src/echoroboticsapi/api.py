import datetime

import pydantic
from aiohttp import ClientSession, ClientResponse
from yarl import URL
from .models import *
import logging
import time


def create_cookies(user_id: str, user_token: str) -> dict[str, str]:
    return {"UserId": user_id, "UserToken": user_token}


class LastKnownMode:
    mode: Mode
    pending_since: float

    def __init__(self, mode: Mode, pending_since: float | None = None):
        self.mode = mode
        self.pending_since = pending_since or time.time()

class Api:
    """Class to make authenticated requests."""

    def __init__(self, websession: ClientSession, robot_ids: RobotId | list[RobotId]):
        """Initialize the auth."""
        self.websession = websession
        if not isinstance(robot_ids, list):
            robot_ids = [robot_ids]
        self.robot_ids = robot_ids
        if len(self.robot_ids) <= 0:
            raise ValueError("must provide a robot id")
        self.logger = logging.getLogger("echoroboticsapi")
        self.smart_modes: dict[RobotId, "SmartMode"] = {}

    def _get_robot_id(self, robot_id: RobotId | None):
        if len(self.robot_ids) > 1 and robot_id is None:
            raise ValueError(
                "more than 1 robot_id is known, please supply the argument robot_id"
            )
        if robot_id is None:
            return self.robot_ids[0]
        else:
            return robot_id

    async def get_config(
        self, reload: bool, robot_id: RobotId | None = None
    ) -> GetConfig:
        """calls GetConfig api endpoint.

        Returns the last known state.
        When called with reload==True, the last state is wiped and fetched again from the robot.
        To get the result, the get_config() must be called again with reload==False a few seconds later
        """
        robot_id = self._get_robot_id(robot_id)

        url = URL(
            f"https://myrobot.echorobotics.com/api/RobotConfig/GetConfig/{robot_id}"
        )
        result = await self.request(method="GET", url=url % {"reload": str(reload)})
        json = await result.json()

        self.logger.debug(f"got json {json}")
        try:
            resp = GetConfig.parse_obj(json)
            return resp
        except pydantic.ValidationError as e:
            self.logger.error(f"error was caused by json {json}")
            self.logger.exception(e)
            raise e

    async def set_mode(self, mode: Mode, robot_id: RobotId | None = None) -> int:
        """Set the operating mode of the robot.

        Returns HTTP status code."""
        robot_id = self._get_robot_id(robot_id)

        result = await self.request(
            method="POST",
            url=URL("https://myrobot.echorobotics.com/api/RobotAction/SetMode"),
            json={
                "Mode": mode,
                "RobotId": robot_id,
            },
        )
        if result.status == 200:
            if robot_id in self.smart_modes[robot_id]:
                self.smart_modes[robot_id].notify_mode_set(mode)
        return result.status

    async def last_statuses(self) -> LastStatuses:
        url_str = "https://myrobot.echorobotics.com/api/RobotData/LastStatuses"

        url_obj = URL(url_str)
        response = await self.request(method="POST", url=url_obj, json=self.robot_ids)

        response.raise_for_status()
        json = await response.json()
        self.logger.debug(f"got json {json}")
        try:
            resp = LastStatuses.parse_obj(json)
        except pydantic.ValidationError as e:
            self.logger.error(f"error was caused by json {json}")
            self.logger.exception(e)
            raise e
        else:
            for si in resp.statuses_info:
                if si.robot in self.smart_modes
                if self.does_status_mean_mowing(si.status):
                    if si.robot not in self._last_known_mode:
                        self._last_known_mode[si.robot] = LastKnownMode(mode="work", pending_since=0)
                    else:

                        self._last_known_mode[si.robot] = "work"
            return resp

    async def request(self, method: str, url: URL, **kwargs) -> ClientResponse:
        """Make a request."""
        return await self.websession.request(
            method,
            url,
            **kwargs,
        )
