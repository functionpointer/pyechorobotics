import datetime

import asyncio
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

    async def set_mode(
        self, mode: Mode, robot_id: RobotId | None = None, use_current: bool = True
    ) -> int:
        """Set the operating mode of the robot.

        Returns HTTP status code, or -1.

        When use_current==True (the default), this method performs multiple calls to current(),
        to evaluate if the set_mode operation worked. This is because the HTTP status code 200 just means the command
        was received by echorobotics.com, but not by the actual robot. If the current() calls failed to verify, this method returns -1.
        The verification process may wait up to 25 seconds for feedback from the actual robot.
        """
        robot_id = self._get_robot_id(robot_id)
        self.logger.debug(
            "set_mode: mode %s for %s; use_current=%s", mode, robot_id, use_current
        )

        oldcurrent = await self.current(robot_id=robot_id)

        result = await self.request(
            method="POST",
            url=URL("https://myrobot.echorobotics.com/api/RobotAction/SetMode"),
            json={
                "Mode": mode,
                "RobotId": robot_id,
            },
        )
        if result.status == 200:
            if use_current:

                def is_confirmed(c: Current) -> bool:
                    if c.action_id == oldcurrent.action_id:
                        return False
                    if c.status != 5:
                        return False
                    expected_modes: dict[Current.Message, Mode] = {
                        Current.Message.scheduled_work: "work",
                        Current.Message.scheduled_work_from_station: "work",
                        Current.Message.scheduled_charge_and_work: "chargeAndWork",
                        Current.Message.scheduled_charge_and_work_from_station: "chargeAndWork",
                        Current.Message.scheduled_charge_and_stay: "chargeAndStay",
                        Current.Message.scheduled_charge_and_stay_from_station: "chargeAndStay",
                    }
                    return (
                        c.message in expected_modes
                        and expected_modes[c.message] == mode
                    )

                verify_start = asyncio.get_running_loop().time()
                newcurrent: Current | None = None
                try:
                    async with asyncio.timeout(25) as timeout:
                        for sleeptime in [3, 2, 2, 2] + [3] * 10:
                            if (
                                timeout.when() - sleeptime
                                < asyncio.get_running_loop().time()
                            ):
                                # not enough time for next sleep
                                raise asyncio.TimeoutError()
                            await asyncio.sleep(sleeptime)
                            newcurrent = await self.current(robot_id)
                            if is_confirmed(newcurrent):
                                break
                            else:
                                self.logger.debug("set_mode verify: %s", newcurrent)
                except asyncio.TimeoutError:
                    # failed to verify :/
                    self.logger.warning(
                        "set_mode %s failed to verify after %ss: %s",
                        mode,
                        asyncio.get_running_loop().time() - verify_start,
                        newcurrent,
                    )
                    return -1
                else:
                    self.logger.info("set_mode successfully verified! %s", newcurrent)

            if robot_id in self.smart_modes:
                await self.smart_modes[robot_id].notify_mode_set(
                    mode, use_current=use_current
                )
            else:
                self.logger.debug(f"set_mode: no smart_mode for robot {robot_id}")
        return result.status

    async def current(self, robot_id: RobotId | None = None) -> Current:
        """Gets the status of the current operation, whatever that means

        Used by set_mode when use_current==True, to verify that the set_mode operation worked
        """

        robot_id = self._get_robot_id(robot_id)
        url = f"https://myrobot.echorobotics.com/api/RobotAction/{robot_id}/current"
        url_obj = URL(url)

        response = await self.request(method="GET", url=url_obj)
        json = await response.json()
        try:
            resp = Current.parse_obj(json)
        except pydantic.ValidationError as e:
            self.logger.error(f"current: error was caused by json {json}")
            self.logger.exception(e)
            raise e
        else:
            if resp.serial_number != robot_id:
                raise ValueError(
                    "current: received different serial_number than requested"
                )
            if robot_id in self.smart_modes:
                await self.smart_modes[robot_id].notify_current_received(resp)
            return resp

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
                    await self.smart_modes[si.robot].notify_laststatuses_received(
                        si.status
                    )
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
