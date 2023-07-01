import datetime

import pydantic
from pydantic import (
    field_validator,
    model_validator,
    BaseModel,
    Field,
    constr,
    Extra,
    validator,
    RootModel,
)
from typing import Literal
from dateutil.parser import isoparse as dateutil_isoparse
from enum import Enum

RobotId = constr()
Mode = Literal["chargeAndWork", "chargeAndStay", "work"]
Status = Literal[
    "Offline",
    "Alarm",
    "Idle",
    "WaitStation",
    "Charge",
    "GoUnloadStation",
    "GoChargeStation",
    "Work",
    "LeaveStation",
    "Off",
    "GoStation",
    "Unknown",
    "Warning",
    "Border",
    "BorderCheck",
    "BorderDiscovery",
]


def dtparse(value) -> datetime.datetime:
    ret = dateutil_isoparse(value)
    is_aware = ret.tzinfo is not None and ret.tzinfo.utcoffset(ret) is not None
    if not is_aware:
        raise ValueError(f"failed to find timezone in: {value}")
    return ret


class Current(BaseModel):
    class Message(str, Enum):
        scheduled_charge_and_work_from_station = (
            "robot.handleActionMessage.scheduledChargeAndWorkFromStation"
        )
        scheduled_work_from_station = (
            "robot.handleActionMessage.scheduledWorkFromStation"
        )
        scheduled_charge_and_stay_from_station = (
            "robot.handleActionMessage.scheduledChargeAndStayFromStation"
        )
        scheduled_charge_and_stay = "robot.handleActionMessage.scheduledChargeAndStay"
        scheduled_work = "robot.handleActionMessage.scheduledWork"
        scheduled_charge_and_work = "robot.handleActionMessage.scheduledChargeAndWork"

        scheduled_charge_and_stay_denied_by_robot = (
            "robot.handleActionMessage.scheduledChargeAndStayDeniedByRobot"
        )

    serial_number: RobotId = Field(..., alias="SerialNumber")
    action_id: int | None = Field(..., alias="ActionId")
    status: pydantic.conint(ge=0, le=5) = Field(..., alias="Status")
    message: Message | str | None = Field(..., alias="Message")


class Position(BaseModel):
    longitude: float = Field(..., alias="Longitude")
    latitude: float = Field(..., alias="Latitude")
    date_time: datetime.datetime = Field(..., alias="DateTime")

    _normalize_date_time = field_validator("date_time", mode="before")(dtparse)


class StatusInfo(BaseModel):
    robot: RobotId = Field(..., alias="Robot")
    status: Status = Field(..., alias="Status")
    mac_address: str = Field(..., alias="MacAddress")
    date: datetime.datetime = Field(..., alias="Date")
    delta: str = Field(..., alias="Delta")
    estimated_battery_level: float = Field(..., alias="EstimatedBatteryLevel")
    position: Position = Field(..., alias="Position")
    query_time: datetime.datetime = Field(..., alias="QueryTime")
    has_values: bool = Field(..., alias="HasValues")
    is_online: bool = Field(..., alias="IsOnline")

    _normalize_date = field_validator("date", mode="before")(dtparse)
    _normalize_query_time = field_validator("query_time", mode="before")(dtparse)


class LastStatuses(BaseModel):
    query_date: datetime.datetime = Field(..., alias="QueryDate")
    robots: list[RobotId] = Field(..., alias="Robots")
    statuses_info: list[StatusInfo] = Field(..., alias="StatusesInfo")
    robot_offline_delay_in_seconds: int = Field(..., alias="RobotOfflineDelayInSeconds")

    _normalize_query_date = field_validator("query_date", mode="before")(dtparse)


class NavigationProfileUserParameters(BaseModel, extra="ignore"):
    robot_name: str = Field(..., alias="RobotName")


class NavigationProfileInstance(BaseModel, extra="ignore"):
    has_gps_rtk: bool = Field(..., alias="HasGpsRTK")
    has_vsb: bool = Field(..., alias="HasVSB")
    user_parameters: NavigationProfileUserParameters = Field(
        ..., alias="UserParameters"
    )


class ServoControlProfileInstance(BaseModel, extra="ignore"):
    current_cutting_height: int = Field(..., alias="CurrentCuttingHeight")


class GetConfigData(BaseModel, extra="ignore"):
    brain_version: str = Field(..., alias="BrainVersion")
    image_version: str = Field(..., alias="ImageVersion")
    navigation_profile_instance: NavigationProfileInstance = Field(
        ..., alias="NavigationProfileInstance"
    )
    servo_control_profile_instance: ServoControlProfileInstance = Field(
        ..., alias="ServoControlProfileInstance"
    )


class GetConfig(BaseModel, extra="ignore"):
    is_error: bool = Field(..., alias="IsError")
    is_in_progress: bool = Field(..., alias="IsInProgress")
    message: str | None = Field(..., alias="Message")
    data: GetConfigData | None = Field(..., alias="Data")
    config_id: int = Field(..., alias="ConfigId")
    config_version_id: int = Field(..., alias="ConfigVersionId")
    config_date_time: datetime.datetime | None = Field(..., alias="ConfigDateTime")
    config_validated: bool = Field(..., alias="ConfigValidated")

    @field_validator("config_date_time", mode="before")
    @classmethod
    def _normalize_config_date_time(cls, v):
        if v == "0001-01-01T00:00:00":
            return None
        else:
            return dtparse(v)

    @model_validator(mode="after")
    @classmethod
    def _check_date_time_none(cls, values):
        if values.get("config_date_time") is None and values.get("config_validated"):
            raise ValueError(f"config_date_time is None, but config_validated is True?")
        return values


class BaseHistoryEvent(BaseModel, extra="ignore"):
    timestamp: datetime.datetime = Field(..., alias="TS")
    duration: datetime.timedelta = Field(..., alias="FD")

    _normalize_timestamp = field_validator("timestamp", mode="before")(dtparse)

    def __lt__(self, other):
        if isinstance(other, BaseHistoryEvent):
            return self.timestamp < other.timestamp
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, BaseHistoryEvent):
            return self.timestamp > other.timestamp
        else:
            return False


class UnknownHistoryEvent(BaseHistoryEvent):
    event: str = Field(..., alias="SE")
    details: str | None = Field(..., alias="D")
    state: str = Field(..., alias="SS")


class KnownHistoryEvent(BaseHistoryEvent):
    state: Status = Field(..., alias="SS")


RemoteSetModeHistoryEventDetails = Literal[
    "Go charge and work", "Go charge and stay", "Start to work"
]


class RemoteSetModeHistoryEvent(KnownHistoryEvent):
    event: Literal["RemoteSetMode"] = Field(..., alias="SE")
    details: RemoteSetModeHistoryEventDetails = Field(..., alias="D")


HistoryEvent = RemoteSetModeHistoryEvent | UnknownHistoryEvent


class HistoryEventCombinedModel(RootModel):
    root: RemoteSetModeHistoryEvent | UnknownHistoryEvent

    def __eq__(self, other):
        if isinstance(other, HistoryEventCombinedModel):
            return self.__root__ == other.__root__
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, HistoryEventCombinedModel):
            return self.__root__.timestamp < other.__root__.timestamp
        else:
            return False

    def __le__(self, other):
        if isinstance(other, HistoryEventCombinedModel):
            return self.__root__.timestamp <= other.__root__.timestamp
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, HistoryEventCombinedModel):
            return self.__root__.timestamp > other.__root__.timestamp
        else:
            return False

    def __ge__(self, other):
        if isinstance(other, HistoryEventCombinedModel):
            return self.__root__.timestamp >= other.__root__.timestamp
        else:
            return False
