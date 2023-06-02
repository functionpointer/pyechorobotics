from pydantic import BaseModel, confloat, Field, constr, Extra
from typing import Literal


DateTimeISO8601 = str
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
]


class Position(BaseModel):
    longitude: float = Field(..., alias="Longitude")
    latitude: float = Field(..., alias="Latitude")
    datetime: DateTimeISO8601 = Field(..., alias="DateTime")


class StatusInfo(BaseModel):
    robot: RobotId = Field(..., alias="Robot")
    status: Status = Field(..., alias="Status")
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


class NavigationProfileUserParameters(BaseModel, extra=Extra.ignore):
    robot_name: str = Field(..., alias="RobotName")


class NavigationProfileInstance(BaseModel, extra=Extra.ignore):
    has_gps_rtk: bool = Field(..., alias="HasGpsRTK")
    has_vsb: bool = Field(..., alias="HasVSB")
    user_parameters: NavigationProfileUserParameters = Field(..., alias="UserParameters")


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
    config_date_time: DateTimeISO8601 = Field(..., alias="ConfigDateTime")
    config_validated: bool = Field(..., alias="ConfigValidated")
