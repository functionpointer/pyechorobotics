import logging
import time

from .api import Api
from .models import RobotId, Status, Mode, HistoryEvent, RemoteSetModeHistoryEvent, RemoteSetModeHistoryEventDetails


class SmartMode:
    """
    Keeps track of which mode the robot is in.
    Unfortunately echoroboticsapi doesn't directly tell us this.
    But we can keep track ourselves and get some hints from last_statuses() and history_list().

    That is what this class does.
    To use, create an instance and register it with your api instance: your_api.register_smart_mode(your_smartmode)

    Keep making api requests to feed the SmartMode instance with data.
    Then you can call get_robot_mode() and get a decent guess.
    """

    def __init__(self, robot_id: RobotId):
        self.robot_id: RobotId = robot_id

        self._last_known_mode: Mode | None = None
        self._mode_known_since: float = 0
        self.logger = logging.getLogger(__name__)

    async def get_robot_mode(self) -> Mode | None:
        """Tries to guess which mode the robot is in

        Keeps track of previous calls of set_mode, and also uses hints from status from last_statuses.
        Does not perform any network calls. Call last_statuses() before for best results.
        Also call history_list() every 15min for best results.
        """
        return self._last_known_mode

    async def notify_mode_set(self, newmode: Mode) -> None:
        self._last_known_mode = newmode
        self._mode_known_since = time.time()

    async def notify_laststatuses_received(self, receivedstatus: Status) -> None:
        ismowing: bool = receivedstatus in ["LeaveStation", "Work"]

        happend_a_while_ago: bool = time.time() < self._mode_known_since + 60
        if ismowing and self._last_known_mode != "work" and happend_a_while_ago:
            self.logger.info(
                "laststatuses: status is %s, inferring modechange from %s to %s",
                receivedstatus,
                self._last_known_mode,
                "work",
            )
            self._last_known_mode = "work"
            self._mode_known_since = time.time()

    async def notify_history_list_received(self, histlist: list[HistoryEvent]) -> None:
        for evt in histlist:
            if isinstance(evt, RemoteSetModeHistoryEvent):
                self.logger.debug("processing %s", evt.timestamp)
                t = evt.timestamp.timestamp()
                modemap: dict[RemoteSetModeHistoryEventDetails, Mode] = {
                    "Go charge and work": "chargeAndWork",
                    "Start to work": "work",
                    "Go charge and stay": "chargeAndStay",
                }
                new_mode = modemap[evt.details]
                if t > self._mode_known_since:
                    self.logger.info("history_list: modechange to %s on %s", new_mode, evt.timestamp)
                    self._last_known_mode = new_mode
                    self._mode_known_since = t
                return
