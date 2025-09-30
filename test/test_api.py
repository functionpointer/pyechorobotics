import datetime
import json
import urllib.parse

import asyncio
import aiohttp

import echoroboticsapi
import pytest
import pytest_asyncio
from aioresponses import aioresponses

from echoroboticsapi import HistoryEvent, RobotId, LastStatuses


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m


@pytest_asyncio.fixture()
async def client_session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def api(client_session: aiohttp.ClientSession, robot_id: echoroboticsapi.RobotId):
    ret = echoroboticsapi.Api(client_session, robot_id)

    def fast():
        while True:
            yield 0.01

    ret._set_mode_use_current_sleep_times = fast
    yield ret


@pytest.mark.asyncio
async def test_get_config(
    robot_id: RobotId, api: echoroboticsapi.Api, mock_aioresponse
):
    mock_json = '{"IsError": true, "IsInProgress": false, "Message": "configurator.messages.robotOffline", "Data": null, "Descriptors": null, "ConfigId": 0, "ConfigVersionId": 0, "ConfigDateTime": "0001-01-01T00:00:00", "ConfigValidated": false}'
    expected_url = f"https://myrobot.echorobotics.com/api/RobotConfig/GetConfig/{robot_id}?reload=False"
    mock_aioresponse.get(expected_url, body=mock_json)

    resp = await api.get_config(reload=False, robot_id=robot_id)

    assert resp
    mock_aioresponse.assert_called_once_with(expected_url, method="GET")


@pytest.mark.asyncio
async def test_laststatuses(
    api: echoroboticsapi.Api, mock_aioresponse, robot_id: echoroboticsapi.RobotId
):
    mock_json = r'{"QueryDate":"2025-01-24T18:50:19.3556944Z","Robots":["robot_id"],"StatusesInfo":[{"Robot":"robot_id","Status":"Off","MacAddress":"ac1f0fb92010","Date":"2024-12-20T15:17:14.861Z","Delta":"5 Wochen","EstimatedBatteryLevel":99.99,"Position":{"Longitude":6.1,"Latitude":5.5,"DateTime":"2024-11-04T13:17:48.461Z"},"QueryTime":"2025-01-24T18:50:19.3556944Z","HasValues":true,"IsOnline":false}],"RobotOfflineDelayInSeconds":1500}'
    mock_json = mock_json.replace("robot_id", robot_id)
    expected_url = "https://myrobot.echorobotics.com/api/RobotData/LastStatuses"
    mock_aioresponse.post(expected_url, body=mock_json)
    last_statuses = await api.last_statuses()

    mock_aioresponse.assert_called_once_with(
        expected_url,
        method="POST",
        json=[robot_id],
    )
    assert last_statuses
    assert last_statuses.statuses_info[0].robot == robot_id
    assert last_statuses.statuses_info[0].position.latitude == 5.5
    assert last_statuses.statuses_info[0].position.longitude == 6.1


@pytest.mark.asyncio
async def test_history_list(
    api: echoroboticsapi.Api, mock_aioresponse, robot_id: echoroboticsapi.RobotId
):
    mock_json = [
        {
            "TS": "1970-01-01T01:52:25.1Z",
            "FD": "00:00:00",
            "SS": "Charge",
            "SE": "WaitChargeComplete",
            "D": "",
        },
        {
            "TS": "1970-01-01T01:52:25Z",
            "FD": "00:00:00.1000000",
            "SS": "Charge",
            "SE": "ChargeStatusChangeEvent",
            "D": "BSoC:15.433056799999999, ChgState:2, StConnect:true, StConnect:true, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T01:52:11Z",
            "FD": "00:00:14",
            "SS": "GoChargeStation",
            "SE": "ChargeStatusChangeEvent",
            "D": "BSoC:15.433056799999999, ChgState:1, StConnect:true, StConnect:true, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T01:52:10Z",
            "FD": "00:00:01",
            "SS": "GoChargeStation",
            "SE": "ChargeStatusChangeEvent",
            "D": "BSoC:15.433056799999999, ChgState:2, StConnect:true, StConnect:true, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T01:52:04Z",
            "FD": "00:00:06",
            "SS": "GoChargeStation",
            "SE": "StationContactDetectedEventArgs",
            "D": "BSoC:15.433056799999999, ChgState:1, StConnect:true, StConnect:true, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T01:50:58Z",
            "FD": "00:01:06",
            "SS": "GoChargeStation",
            "SE": "TrackWire",
            "D": "",
        },
        {
            "TS": "1970-01-01T01:50:58Z",
            "FD": "00:00:00",
            "SS": "GoChargeStation",
            "SE": "ChangeParcelCompleteEventArgs",
            "D": "Parcel Loop reached. Previous parcel: PARCELNAME.",
        },
        {
            "TS": "1970-01-01T01:50:53Z",
            "FD": "00:00:05",
            "SS": "GoChargeStation",
            "SE": "ChangeFieldCompleteEventArgs",
            "D": "Field Draht CH5 reached. Previous field: Draht CH0.",
        },
        {
            "TS": "1970-01-01T01:50:33Z",
            "FD": "00:00:20",
            "SS": "GoChargeStation",
            "SE": "TrackBorder",
            "D": "Track distance: 10.02",
        },
        {
            "TS": "1970-01-01T01:48:04Z",
            "FD": "00:02:29",
            "SS": "GoChargeStation",
            "SE": "GPSPath",
            "D": "5.5,6.7 5.6,6.1 5.4,6.3 5.8,6.2 ",
        },
        {
            "TS": "1970-01-01T01:48:02Z",
            "FD": "00:00:02",
            "SS": "GoChargeStation",
            "SE": "GoBaseStation",
            "D": "",
        },
        {
            "TS": "1970-01-01T01:48:02Z",
            "FD": "00:00:00",
            "SS": "Work",
            "SE": "CycleHeadStatusEvent",
            "D": "H1 : 1.1 RPS, 0.1 A, H2 : 1.1 RPS, 1.1 A, H3 : 1.1 RPS, 1.1 A, ",
        },
        {
            "TS": "1970-01-01T01:48:02Z",
            "FD": "00:00:00",
            "SS": "Work",
            "SE": "CycleStats",
            "D": '{ CurrentParcel: "GPS PARCELNAME", CycleDuration_sec: 7902, CuttingHeight: 25, AvgPowerConso: 4.644813, AvgToolConso: 1.597533, AvgTheoreticalCuttingHeadConso 1.295319, AvgCuttingTotalConso: 1.614316, MaxSpeed: 0.8, AvgSpeedLeftWheel: 0.5405058, AvgSpeedRightWheel: 0.531204, AvgCurrentLeftWheel: 1.378346, AvgCurrentRightWheel: 1.168933, AvgTractionSpeed: 0.7019057, AvgTargetSpeedCoil: 0.7969443, AvgtargetSpeedSonars: 0.7469826, AvgCuttingAdaptSpeed: 0.7882863, AvgCuttingHeadConso: 4.842947, WireBouncesCount: 0, CollisionsCount: 0, TrackLineCount: 66 }',
        },
        {
            "TS": "1970-01-01T01:48:02Z",
            "FD": "00:00:00",
            "SS": "Work",
            "SE": "BatteryChargeStatus",
            "D": "BSoC: 17.72036, CellVLow: 3.136, BatteryCellVoltageNeedCharge 3.21, AvgCurr: -7.336638, TBat: 27, ChargeOffset: 0",
        },
        {
            "TS": "1970-01-01T01:48:02Z",
            "FD": "00:00:00",
            "SS": "Work",
            "SE": "ChargeStatusChangeEvent",
            "D": "BSoC:17.720359999999999, ChgState:1, StConnect:false, StConnect:false, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T21:56:12Z",
            "FD": "00:51:50",
            "SS": "Work",
            "SE": "PoseTrustRecoveredEvent",
            "D": "Pose=(5.9, 6.4 H=0.1), RTKQuality=Fixed-RTK, SafeDistance=-15.30, RtkStationSignatureNotEqual, BorderSignatureTimeout, BorderPairedSignatureTimeout, BorderDistancesTimeout, BorderPairedDistancesTimeout, BorderDistanceSoftTimeout",
        },
        {
            "TS": "1970-01-01T21:56:07Z",
            "FD": "00:00:05",
            "SS": "Work",
            "SE": "RtkSvinChange",
            "D": "oldX:40.2, oldY:482.1, oldZ:49.2, oldId:0, newX:40.1, newY:443.9, newZ:4.2, newId:0, ",
        },
        {
            "TS": "1970-01-01T21:48:15Z",
            "FD": "00:07:52",
            "SS": "Idle",
            "SE": "RTKRecovering",
            "D": "RTKRecovering",
        },
        {
            "TS": "1970-01-01T21:43:14Z",
            "FD": "00:05:01",
            "SS": "Idle",
            "SE": "WaitUntilPoseIsTrustedEvent",
            "D": "Pose=(5.6, 6.2 H=0.1), RTKQuality=Non-RTK, SafeDistance=-1.50, RtkStationCorrectionTimeout, RtkStationSignatureNotEqual, BorderSignatureTimeout, BorderPairedSignatureTimeout, BorderDistancesTimeout, BorderPairedDistancesTimeout, GpsQualityLow, BorderDistanceSoftTimeout",
        },
        {
            "TS": "1970-01-01T21:42:18Z",
            "FD": "00:00:56",
            "SS": "Work",
            "SE": "PoseTrustRecoveredEvent",
            "D": "Pose=(5.6, 6.3 H=0.2), RTKQuality=Fixed-RTK, SafeDistance=-1.00, RtkStationSignatureNotEqual, BorderSignatureTimeout, BorderPairedSignatureTimeout, BorderDistancesTimeout, BorderPairedDistancesTimeout, BorderDistanceSoftTimeout",
        },
        {
            "TS": "1970-01-01T21:42:12Z",
            "FD": "00:00:06",
            "SS": "Idle",
            "SE": "WaitUntilPoseIsTrustedEvent",
            "D": "Pose=(5.5, 6.7 H=1.80), RTKQuality=Non-RTK, SafeDistance=-16.00, RtkStationCorrectionTimeout, RtkStationSignatureNotEqual, BorderSignatureTimeout, BorderPairedSignatureTimeout, BorderDistancesTimeout, BorderPairedDistancesTimeout, GpsQualityLow, BorderDistanceSoftTimeout",
        },
        {
            "TS": "1970-01-01T20:40:17Z",
            "FD": "01:01:55",
            "SS": "Work",
            "SE": "StartOfPattern",
            "D": "StartOfPattern",
        },
        {
            "TS": "1970-01-01T20:36:21Z",
            "FD": "00:03:56",
            "SS": "Work",
            "SE": "GPSPath",
            "D": "5.4,6.4 5.7,6.7 5.7,6.29 5.5,6.6 5.5,6.5 5.2,6.8 5.2,6.3 ",
        },
        {
            "TS": "1970-01-01T20:36:19Z",
            "FD": "00:00:02",
            "SS": "Work",
            "SE": "RandomProcessAreaTaskStartEvent",
            "D": "Active Heads : -1-2-3, Height: 25, Parcel : GPS PARCELNAME",
        },
        {
            "TS": "1970-01-01T20:36:19Z",
            "FD": "00:00:00",
            "SS": "LeaveStation",
            "SE": "ChangeParcelCompleteEventArgs",
            "D": "Parcel PARCELNAME reached. Previous parcel: Loop.",
        },
        {
            "TS": "1970-01-01T20:36:19Z",
            "FD": "00:00:00",
            "SS": "LeaveStation",
            "SE": "ChangeFieldCompleteEventArgs",
            "D": "Field Draht CH0 reached. Previous field: Draht CH5.",
        },
        {
            "TS": "1970-01-01T20:36:04Z",
            "FD": "00:00:15",
            "SS": "LeaveStation",
            "SE": "TrackWire",
            "D": "",
        },
        {
            "TS": "1970-01-01T20:35:49Z",
            "FD": "00:00:15",
            "SS": "LeaveStation",
            "SE": "StationContactLostEventArgs",
            "D": "BSoC:100, ChgState:0, StConnect:false, StConnect:false, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T20:35:47Z",
            "FD": "00:00:02",
            "SS": "LeaveStation",
            "SE": "TrackWire",
            "D": "",
        },
        {
            "TS": "1970-01-01T20:35:47Z",
            "FD": "00:00:00",
            "SS": "LeaveStation",
            "SE": "ExitStation",
            "D": "",
        },
        {
            "TS": "1970-01-01T20:35:40Z",
            "FD": "00:00:07",
            "SS": "WaitStation",
            "SE": "ChooseParcel",
            "D": " ( [GPS PARCELNAME(tgt: 100):  eff: 100.00, err: 0.00%] [GPS PARCELNAME(tgt: 100): finished pattern,  forced: False] ) => (F2) Draht CH0 / (P100) GPS PARCELNAME",
        },
        {
            "TS": "1970-01-01T20:35:40Z",
            "FD": "00:00:00",
            "SS": "WaitStation",
            "SE": "RobotStatusChanged",
            "D": "Charge completed",
        },
        {
            "TS": "1970-01-01T20:35:40Z",
            "FD": "00:00:00",
            "SS": "Charge",
            "SE": "BatteryBalancingEvent",
            "D": "No need for balancing:vcellhi : 3.44V vcelllo : 3.408V ",
        },
        {
            "TS": "1970-01-01T20:35:40Z",
            "FD": "00:00:00",
            "SS": "Charge",
            "SE": "ChargeStatusChangeEvent",
            "D": "BSoC:100, ChgState:3, StConnect:true, StConnect:true, Nb_Just_Chged:1, ",
        },
        {
            "TS": "1970-01-01T19:15:05.1Z",
            "FD": "01:20:34.9000000",
            "SS": "Charge",
            "SE": "WaitChargeComplete",
            "D": "",
        },
        {
            "TS": "1970-01-01T19:15:05Z",
            "FD": "00:00:00.1000000",
            "SS": "Charge",
            "SE": "ChargeStatusChangeEvent",
            "D": "BSoC:18.473451600000001, ChgState:2, StConnect:true, StConnect:true, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T19:14:51Z",
            "FD": "00:00:14",
            "SS": "GoChargeStation",
            "SE": "ChargeStatusChangeEvent",
            "D": "BSoC:18.473451600000001, ChgState:1, StConnect:true, StConnect:true, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T19:14:51Z",
            "FD": "00:00:00",
            "SS": "GoChargeStation",
            "SE": "ChargeStatusChangeEvent",
            "D": "BSoC:18.473451600000001, ChgState:2, StConnect:true, StConnect:true, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T19:14:45Z",
            "FD": "00:00:06",
            "SS": "GoChargeStation",
            "SE": "StationContactDetectedEventArgs",
            "D": "BSoC:18.473451600000001, ChgState:1, StConnect:true, StConnect:true, Nb_Just_Chged:0, ",
        },
        {
            "TS": "1970-01-01T19:12:05Z",
            "FD": "00:02:40",
            "SS": "GoChargeStation",
            "SE": "TrackWire",
            "D": "",
        },
        {
            "TS": "1970-01-01T19:12:05Z",
            "FD": "00:00:00",
            "SS": "GoChargeStation",
            "SE": "ChangeParcelCompleteEventArgs",
            "D": "Parcel Loop reached. Previous parcel: PARCELNAME.",
        },
    ]
    mock_json = json.dumps(mock_json)
    date_from = datetime.datetime(year=1970, month=1, day=1)
    date_to = datetime.datetime(year=1970, month=1, day=3)
    ftime = "%Y-%m-%dT%H:%M:%S"
    args = urllib.parse.urlencode(
        {
            "DateFrom": date_from.strftime(ftime),
            "DateTo": date_to.strftime(ftime),
            "SerialNumber": robot_id,
        }
    )
    expected_url = f"https://myrobot.echorobotics.com/api/History/list?{args}"

    mock_aioresponse.get(expected_url, body=mock_json)

    history_list: list[HistoryEvent] = await api.history_list(
        date_from=date_from, date_to=date_to
    )

    assert history_list
    mock_aioresponse.assert_called_once_with(
        expected_url,
        method="GET",
    )
    assert len(history_list) > 3


@pytest.mark.asyncio
async def test_current(
    api: echoroboticsapi.Api, mock_aioresponse, robot_id: echoroboticsapi.RobotId
):
    mock_json = r'{"SerialNumber":"robot_id","ActionId":null,"Status":0,"Message":null}'
    mock_json = mock_json.replace("robot_id", robot_id)
    expected_url = (
        f"https://myrobot.echorobotics.com/api/RobotAction/{robot_id}/current"
    )
    mock_aioresponse.get(expected_url, body=mock_json)

    current = await api.current()

    assert current
    mock_aioresponse.assert_called_once_with(
        expected_url,
        method="GET",
    )


@pytest.mark.asyncio
async def test_set_mode_bad_contact(
    api: echoroboticsapi.Api, mock_aioresponse, robot_id: echoroboticsapi.RobotId
):
    mock_json_old = (
        rf'{{"SerialNumber":"{robot_id}","ActionId":null,"Status":0,"Message":null}}'
    )
    mock_json_pending = rf'{{"SerialNumber":"{robot_id}"}}'
    mock_json_error = rf'{{"SerialNumber":"{robot_id}","ActionId":123456,"Status":6,"Message":"robotActionErrorMessages.contactError"}}'
    expected_url = (
        f"https://myrobot.echorobotics.com/api/RobotAction/{robot_id}/current"
    )
    setmode_url = "https://myrobot.echorobotics.com/api/RobotAction/SetMode"
    mock_aioresponse.get(expected_url, body=mock_json_old, repeat=1)
    mock_aioresponse.post(setmode_url)
    mock_aioresponse.get(expected_url, body=mock_json_pending, repeat=3)
    mock_aioresponse.get(expected_url, body=mock_json_error, repeat=1)

    status_code = await api.set_mode("work", robot_id, use_current=True)

    assert status_code == -1
    mock_aioresponse.assert_called_with(expected_url, method="GET")


@pytest.mark.asyncio
async def test_set_mode_bad_contact_timeout(
    api: echoroboticsapi.Api, mock_aioresponse, robot_id: echoroboticsapi.RobotId
):
    mock_json_old = (
        rf'{{"SerialNumber":"{robot_id}","ActionId":null,"Status":0,"Message":null}}'
    )
    mock_json_pending = rf'{{"SerialNumber":"{robot_id}"}}'
    expected_url = (
        f"https://myrobot.echorobotics.com/api/RobotAction/{robot_id}/current"
    )
    setmode_url = "https://myrobot.echorobotics.com/api/RobotAction/SetMode"
    mock_aioresponse.get(expected_url, body=mock_json_old, repeat=1)
    mock_aioresponse.post(setmode_url)
    mock_aioresponse.get(expected_url, body=mock_json_pending, repeat=True)

    status_code = await api.set_mode(
        "work", robot_id, use_current=True, use_current_timeout=0.3
    )

    assert status_code == -1
    mock_aioresponse.assert_called_with(expected_url, method="GET")


@pytest.mark.asyncio
async def test_set_mode_working(
    api: echoroboticsapi.Api, mock_aioresponse, robot_id: echoroboticsapi.RobotId
):
    mock_json_old = (
        rf'{{"SerialNumber":"{robot_id}","ActionId":null,"Status":0,"Message":null}}'
    )
    mock_json_pending1 = rf'{{"SerialNumber":"{robot_id}"}}'
    mock_json_pending2 = (
        rf'{{"SerialNumber":"{robot_id}", "ActionId":123456, "Status": 2}}'
    )
    mock_json_success = rf'{{"SerialNumber":"{robot_id}","ActionId":123456,"Status":6,"Message":"robot.handleActionMessage.scheduledWork"}}'
    expected_url = (
        f"https://myrobot.echorobotics.com/api/RobotAction/{robot_id}/current"
    )
    setmode_url = "https://myrobot.echorobotics.com/api/RobotAction/SetMode"
    mock_aioresponse.get(expected_url, body=mock_json_old, repeat=1)
    mock_aioresponse.post(setmode_url)
    mock_aioresponse.get(expected_url, body=mock_json_pending1, repeat=1)
    mock_aioresponse.get(expected_url, body=mock_json_pending2, repeat=1)
    mock_aioresponse.get(expected_url, body=mock_json_success, repeat=1)

    status_code = await api.set_mode("work", robot_id, use_current=True)

    assert status_code == 200
    mock_aioresponse.assert_called_with(expected_url, method="GET")
