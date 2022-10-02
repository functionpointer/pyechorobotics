import datetime

import pydantic
from aiohttp import ClientSession, ClientResponse
from yarl import URL
from .models import *
import logging


def create_cookies(user_id: str, user_token: str) -> dict[str, str]:
    return {"UserId": user_id, "UserToken": user_token}


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

    async def set_mode(
        self, mode: Mode, robot_id: RobotId | None = None
    ) -> int:
        """Set the operating mode of the robot.

        Returns HTTP status code."""
        if len(self.robot_ids) > 1 and robot_id is None:
            raise ValueError(
                "more than 1 robot_id is known, please supply the argument robot_id"
            )

        result = await self.request(
            method="POST",
            url=URL("https://myrobot.echorobotics.com/api/RobotAction/SetMode"),
            json={"Mode": mode, "RobotId": robot_id if robot_id is not None else self.robot_ids[0]},
        )
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
            return resp
        except pydantic.ValidationError as e:
            self.logger.error(f"error was caused by json {json}")
            self.logger.exception(e)
            raise e

    async def request(self, method: str, url: URL, **kwargs) -> ClientResponse:
        """Make a request."""
        return await self.websession.request(
            method,
            url,
            **kwargs,
        )
