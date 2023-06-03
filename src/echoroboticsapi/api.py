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

    def register_smart_mode(self, smartmode: "SmartMode"):
        self.smart_modes[smartmode.robot_id] = smartmode

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
        self.logger.debug("set_mode: mode %s for %s", mode, robot_id)

        result = await self.request(
            method="POST",
            url=URL("https://myrobot.echorobotics.com/api/RobotAction/SetMode"),
            json={
                "Mode": mode,
                "RobotId": robot_id,
            },
        )
        if result.status == 200:
            if robot_id in self.smart_modes:
                await self.smart_modes[robot_id].notify_mode_set(mode)
            else:
                self.logger.debug(f"set_mode: no smart_mode for robot {robot_id}")
        return result.status

    async def last_statuses(self) -> LastStatuses:
        url_str = "https://myrobot.echorobotics.com/api/RobotData/LastStatuses"

        url_obj = URL(url_str)
        response = await self.request(method="POST", url=url_obj, json=self.robot_ids)

        response.raise_for_status()
        json = await response.json()
        self.logger.debug(f"last_statuses: got json {json}")
        try:
            resp = LastStatuses.parse_obj(json)
        except pydantic.ValidationError as e:
            self.logger.error(f"last_statuses: error was caused by json {json}")
            self.logger.exception(e)
            raise e
        else:
            for si in resp.statuses_info:
                if si.robot in self.smart_modes:
                    await self.smart_modes[si.robot].notify_laststatuses_received(si.status)
            return resp

    async def history_list(
        self,
        robot_id: RobotId | None = None,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
    ) -> list[HistoryEvent]:
        """Gets list of recent events, ordered by newest first.

        Unfortunately this isn't that quick. You may have to wait 15mins for a new event to show up here.
        """
        robot_id = self._get_robot_id(robot_id)
        if date_from is None:
            date_from = datetime.datetime.now() - datetime.timedelta(hours=16)
        if date_to is None:
            date_to = datetime.datetime.now() + datetime.timedelta(hours=2)
        url = URL("https://myrobot.echorobotics.com/api/History/list")
        ftime = "%Y-%m-%dT%H:%M:%S"

        response = await self.request(
            method="GET",
            url=url
            % {
                "DateFrom": date_from.strftime(ftime),
                "DateTo": date_to.strftime(ftime),
                "SerialNumber": robot_id,
            },
        )
        json = await response.json()
        try:
            resp = []
            for obj in json:
                self.logger.debug("history_list: parsing %s", obj)
                parsed = HistoryEventCombinedModel.parse_obj(obj)
                self.logger.debug("history_list: success: %s", parsed)
                resp.append(parsed)
        except pydantic.ValidationError as e:
            self.logger.error(f"history_list: error was caused by json {json}")
            self.logger.exception(e)
            raise e
        else:
            # https://stackoverflow.com/questions/3755136/pythonic-way-to-check-if-a-list-is-sorted-or-not
            is_sorted = all(resp[i] >= resp[i + 1] for i in range(len(resp) - 1))
            if not is_sorted:
                self.logger.warning("history_list: isn't sorted!")

            resp = [q.__root__ for q in resp]

            if robot_id in self.smart_modes:
                await self.smart_modes[robot_id].notify_history_list_received(resp)
            return resp

    async def request(self, method: str, url: URL, **kwargs) -> ClientResponse:
        """Make a request."""
        return await self.websession.request(
            method,
            url,
            **kwargs,
        )
