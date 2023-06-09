import datetime

import pydantic
from pydantic import BaseModel, Field, constr, Extra, validator
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
    is_aware = ret.tzinfo is not None and ret.tzinfo.utcoffset(d) is not None
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

    serial_number: RobotId = Field(..., alias="SerialNumber")
    action_id: int | None = Field(..., alias="ActionId")
    status: pydantic.conint(ge=0, le=5) = Field(..., alias="Status")
    message: Message | str | None = Field(..., alias="Message")


class Position(BaseModel):
    longitude: float = Field(..., alias="Longitude")
    latitude: float = Field(..., alias="Latitude")
    date_time: datetime.datetime = Field(..., alias="DateTime")

    _normalize_date_time = validator("date_time", pre=True, allow_reuse=True)(dtparse)


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

    _normalize_date = validator("date", pre=True, allow_reuse=True)(dtparse)
    _normalize_query_time = validator("query_time", pre=True, allow_reuse=True)(dtparse)


class LastStatuses(BaseModel):
    query_date: datetime.datetime = Field(..., alias="QueryDate")
    robots: list[RobotId] = Field(..., alias="Robots")
    statuses_info: list[StatusInfo] = Field(..., alias="StatusesInfo")
    robot_offline_delay_in_seconds: int = Field(..., alias="RobotOfflineDelayInSeconds")

    _normalize_query_date = validator("query_date", pre=True, allow_reuse=True)(dtparse)


class NavigationProfileUserParameters(BaseModel, extra=Extra.ignore):
    robot_name: str = Field(..., alias="RobotName")


class NavigationProfileInstance(BaseModel, extra=Extra.ignore):
    has_gps_rtk: bool = Field(..., alias="HasGpsRTK")
    has_vsb: bool = Field(..., alias="HasVSB")
    user_parameters: NavigationProfileUserParameters = Field(
        ..., alias="UserParameters"
    )


class ServoControlProfileInstance(BaseModel, extra=Extra.ignore):
    current_cutting_height: int = Field(..., alias="CurrentCuttingHeight")


class GetConfigData(BaseModel, extra=Extra.ignore):
    brain_version: str = Field(..., alias="BrainVersion")
    image_version: str = Field(..., alias="ImageVersion")
    navigation_profile_instance: NavigationProfileInstance = Field(
        ..., alias="NavigationProfileInstance"
    )
    servo_control_profile_instance: ServoControlProfileInstance = Field(
        ..., alias="ServoControlProfileInstance"
    )


class GetConfig(BaseModel, extra=Extra.ignore):
    is_error: bool = Field(..., alias="IsError")
    is_in_progress: bool = Field(..., alias="IsInProgress")
    message: str | None = Field(..., alias="Message")
    data: GetConfigData | None = Field(..., alias="Data")
    config_id: int = Field(..., alias="ConfigId")
    config_version_id: int = Field(..., alias="ConfigVersionId")
    config_date_time: datetime.datetime = Field(..., alias="ConfigDateTime")
    config_validated: bool = Field(..., alias="ConfigValidated")

    _normalize_config_date_time = validator(
        "config_date_time", pre=True, allow_reuse=True
    )(dtparse)


class BaseHistoryEvent(BaseModel, extra=Extra.ignore):
    timestamp: datetime.datetime = Field(..., alias="TS")
    duration: datetime.timedelta = Field(..., alias="FD")

    _normalize_timestamp = validator("timestamp", pre=True, allow_reuse=True)(dtparse)

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


class HistoryEventCombinedModel(BaseModel):
    __root__: RemoteSetModeHistoryEvent | UnknownHistoryEvent

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
