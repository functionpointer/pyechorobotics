from pydantic import BaseModel, confloat, Field, constr
from typing import Literal


DateTimeISO8601 = str
RobotId = constr()
Mode = Literal["chargeAndWork", "chargeAndStay", "work"]

class Position(BaseModel):
    longitude: float = Field(..., alias="Longitude")
    latitude: float = Field(..., alias="Latitude")
    datetime: DateTimeISO8601 = Field(..., alias="DateTime")


class StatusInfo(BaseModel):
    robot: RobotId = Field(..., alias="Robot")
    status: Literal["WaitStation", "Idle", "Work", "Charge"] = Field(..., alias="Status")
    mac_address: str = Field(..., alias="MacAddress")
    date: DateTimeISO8601 = Field(..., alias="Date")
    delta: str = Field(..., alias="Delta")
    estimated_battery_level: float = Field(..., alias="EstimatedBatteryLevel")
    position: Position = Field(..., alias="Position")
    query_time: DateTimeISO8601 = Field(..., alias="QueryTime")
    has_values: bool = Field(..., alias="HasValues")
    is_online: bool = Field(..., alias="IsOnline")


class LastStatuses(BaseModel):
    query_date: DateTimeISO8601 = Field(..., alias="QueryDate")
    robots: list[RobotId] = Field(..., alias="Robots")
    statuses_info: list[StatusInfo] = Field(..., alias="StatusesInfo")
    robot_offline_delay_in_seconds: int = Field(..., alias="RobotOfflineDelayInSeconds")
