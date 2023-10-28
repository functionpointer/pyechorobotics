import logging

from echoroboticsapi import Api, RobotId, Status
import time


class SmartFetch:
    def __init__(self, api: Api, fetch_history_wait_time: float = 60 * 15):
        self.logger = logging.getLogger(__name__)

        self.api = api
        self.fetch_history_wait_time = fetch_history_wait_time
        self.fetch_history_times: dict[RobotId, float] = {}

    async def smart_fetch(self):
        """Intended for use in conjunction with smart_mode. Calls last_statuses and returns results.
        Also interprets the result and calls history_list if beneficial.

        """

        statuses_requiring_history_list: list[Status] = [
            "Charge",
            "GoUnloadStation",
            "GoChargeStation",
            "GoStation",
        ]
        statuses = await self.api.last_statuses()

        for statusinfo in statuses.statuses_info:
            robot_id = statusinfo.robot
            if robot_id not in self.fetch_history_times:
                self.fetch_history_times[robot_id] = -1

            if statusinfo.status in statuses_requiring_history_list:
                if self.fetch_history_times[robot_id] <= 0:
                    self.fetch_history_times[robot_id] = (
                        time.time() + self.fetch_history_wait_time
                    )
                    self.logger.info(f"schedule fetch_history for {robot_id}")
                elif self.fetch_history_times[robot_id] < time.time():
                    self.logger.info(f"fetching history for {robot_id}")
                    self.fetch_history_times[robot_id] = (
                        time.time() + self.fetch_history_wait_time
                    )

                    await self.api.history_list(robot_id)
                else:
                    # don't fetch history, wait_time has not elapsed yet
                    pass
            else:
                if self.fetch_history_times[robot_id] > 0:
                    self.logger.info(f"cancelling fetch_history for {robot_id}")
                else:
                    self.logger.debug(f"not scheduling fetch_history for %s", robot_id)
                self.fetch_history_times[robot_id] = -1

        return statuses
