from .api import Api
from models import RobotId, Status, Mode


def does_status_mean_mowing(self, status: Status) -> bool:
    """Returns true if this status means the mower is or will be actively mowing.

    Used by smart_get_robot_state internally
    """
    mowing_states = ["LeaveStation", "Work"]
    return status in mowing_states


class SmartMode:
    def __init__(self, api: Api, robot_id: RobotId):
        self.api = Api
        self.robot_id = RobotId

        self._last_known_mode: Mode | None = None
        self._mode_known_since: float = 0

    async def get_robot_state(self) -> Mode | None:
        """Tries to guess which mode the robot is in

        Keeps track of previous calls of set_mode, and also uses hints from status from last_statuses.
        Does not perform any network calls. Call last_statuses() before for best results.
        """
        return self._last_known_mode

    def notify_mode_set(self, newmode: Mode) -> None:
        pass

    def notify_laststatuses_received(self, receivedstatus: Status) -> None:
        pass
