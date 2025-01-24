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
    "OffAfterAlarm",
]


def dtparse(value) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        return value
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
        scheduled_work_denied_by_robot = (
            "robot.handleActionMessage.scheduledWorkDeniedByRobot"
        )
        already_in_work = "robot.handleActionMessage.alreadyInWork"

    serial_number: RobotId = Field(..., alias="SerialNumber")
    action_id: int | None = Field(..., alias="ActionId")
    status: pydantic.conint(ge=0, le=6) = Field(..., alias="Status")
    message: Message | str | None = Field(..., alias="Message")


class Position(BaseModel):
    longitude: float = Field(..., serialization_alias="Longitude")
    latitude: float = Field(..., serialization_alias="Latitude")
    date_time: datetime.datetime = Field(..., serialization_alias="DateTime")

    _normalize_date_time = field_validator("date_time", mode="before")(dtparse)


class StatusInfo(BaseModel):
    robot: RobotId = Field(..., serialization_alias="Robot")
    status: Status = Field(..., serialization_alias="Status")
    mac_address: str = Field(..., serialization_alias="MacAddress")
    date: datetime.datetime = Field(..., serialization_alias="Date")
    delta: str = Field(..., serialization_alias="Delta")
    estimated_battery_level: float = Field(..., serialization_alias="EstimatedBatteryLevel")
    position: Position = Field(..., serialization_alias="Position")
    query_time: datetime.datetime = Field(..., serialization_alias="QueryTime")
    has_values: bool = Field(..., serialization_alias="HasValues")
    is_online: bool = Field(..., serialization_alias="IsOnline")

    _normalize_date = field_validator("date", mode="before")(dtparse)
    _normalize_query_time = field_validator("query_time", mode="before")(dtparse)


class LastStatuses(BaseModel):
    query_date: datetime.datetime = Field(..., serialization_alias="QueryDate")
    robots: list[RobotId] = Field(..., serialization_alias="Robots")
    statuses_info: list[StatusInfo] = Field(..., serialization_alias="StatusesInfo")
    robot_offline_delay_in_seconds: int = Field(..., serialization_alias="RobotOfflineDelayInSeconds")

    _normalize_query_date = field_validator("query_date", mode="before")(dtparse)


class NavigationProfileUserParameters(BaseModel, extra="ignore"):
    robot_name: str = Field(..., serialization_alias="RobotName")


class NavigationProfileInstance(BaseModel, extra="ignore"):
    has_gps_rtk: bool = Field(..., serialization_alias="HasGpsRTK")
    has_vsb: bool = Field(..., serialization_alias="HasVSB")
    user_parameters: NavigationProfileUserParameters = Field(
        ..., serialization_alias="UserParameters"
    )


class ServoControlProfileInstance(BaseModel, extra="ignore"):
    current_cutting_height: int = Field(..., serialization_alias="CurrentCuttingHeight")


class GetConfigData(BaseModel, extra="ignore"):
    brain_version: str = Field(..., serialization_alias="BrainVersion")
    image_version: str = Field(..., serialization_alias="ImageVersion")
    navigation_profile_instance: NavigationProfileInstance = Field(
        ..., serialization_alias="NavigationProfileInstance"
    )
    servo_control_profile_instance: ServoControlProfileInstance = Field(
        ..., serialization_alias="ServoControlProfileInstance"
    )


class GetConfig(BaseModel, extra="ignore"):
    is_error: bool = Field(..., serialization_alias="IsError")
    is_in_progress: bool = Field(..., serialization_alias="IsInProgress")
    message: str | None = Field(..., serialization_alias="Message")
    data: GetConfigData | None = Field(..., serialization_alias="Data")
    config_id: int = Field(..., serialization_alias="ConfigId")
    config_version_id: int = Field(..., serialization_alias="ConfigVersionId")
    config_date_time: datetime.datetime | None = Field(..., serialization_alias="ConfigDateTime")
    config_validated: bool = Field(..., serialization_alias="ConfigValidated")

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
    timestamp: datetime.datetime = Field(..., serialization_alias="TS")
    duration: datetime.timedelta = Field(..., serialization_alias="FD")

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
    event: str = Field(..., serialization_alias="SE")
    details: str | None = Field(..., serialization_alias="D")
    state: str = Field(..., serialization_alias="SS")


class KnownHistoryEvent(BaseHistoryEvent):
    state: Status = Field(..., serialization_alias="SS")


RemoteSetModeHistoryEventDetails = Literal[
    "Go charge and work", "Go charge and stay", "Start to work"
]


class RemoteSetModeHistoryEvent(KnownHistoryEvent):
    event: Literal["RemoteSetMode"] = Field(..., serialization_alias="SE")
    details: RemoteSetModeHistoryEventDetails = Field(..., serialization_alias="D")


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
