import asyncio
import datetime
import json

import aiohttp

NIU_LOGIN_URL = "https://account-fk.niu.com"
NIU_API_URL = "https://app-api-fk.niu.com"

HTTP_HEADER = {
    "User-Agent": "manager/4.1.0 (android; NoPhone 1 9);lang=it-IT;clientIdentifier=Overseas;timezone=Europe/Rome;brand=NoPhone 1;model=NoPhone 1;osVersion=9;pixels=1080x1920",
    # 'User-Agent': 'lang={};clientIdentifier=Overseas',
    "Content-Type": "application/x-www-form-urlencoded",
}


class Session:
    username = ""
    password = ""
    lang = ""
    token = ""
    vehicles = {}


SESSION = Session()


class NiuCloud:
    def __init__(self, username=None, password=None, token=None, lang="en-US"):
        SESSION.username = username
        SESSION.password = password
        SESSION.token = token
        SESSION.lang = lang

        HTTP_HEADER["User-Agent"] = HTTP_HEADER["User-Agent"].format(lang)

    async def connect(self):
        await self.check_access_token()
        return self.token

    @property
    def token(self):
        return SESSION.token

    async def get_new_token(self):
        if SESSION.username == "" or SESSION.password == "":
            raise NiuAPIException("Can't find username or password")

        resp = await self._request(
            "POST",
            NIU_LOGIN_URL + "/appv2/login",
            data={"account": SESSION.username, "password": SESSION.password},
        )
        SESSION.token = resp["data"]["token"]

    async def check_access_token(self):
        if not SESSION.token:
            await self.get_new_token()

    async def update_vehicles(self):
        await self.check_access_token()

        resp = await self._request(
            "GET",
            NIU_API_URL + "/v5/scooter/list",
        )
        vehicles = resp["data"]["items"]
        updated = []

        for vehicle in vehicles:
            veh = SESSION.vehicles.get(vehicle["sn_id"])
            if veh == None:
                veh = Vehicle()

            veh.update(vehicle)

            resp = await self._request(
                "GET",
                NIU_API_URL + f"/v5/scooter/detail/{veh.serial_number}",
            )
            veh.update(resp["data"])

            # Get general details
            resp = await self._request(
                "GET",
                NIU_API_URL + "/v3/motor_data/index_info",
                params={"sn": veh.serial_number},
            )
            veh.update(resp["data"])

            # Get vehicle status
            resp = await self._request(
                "GET",
                NIU_API_URL + "/v3/motor_data/index_info",
                params={"sn": veh.serial_number},
            )
            veh.update(resp["data"])

            # Get battery status
            resp = await self._request(
                "GET",
                NIU_API_URL + "/v3/motor_data/battery_info",
                params={"sn": veh.serial_number},
                data={"sn": veh.serial_number, "token": SESSION.token},
            )
            veh.update(resp["data"])

            # Get odometer
            resp = await self._request(
                "POST",
                NIU_API_URL + "/motoinfo/overallTally",
                params={"sn": veh.serial_number},
                data={"sn": veh.serial_number, "token": SESSION.token},
            )
            veh.update(resp["data"])

            SESSION.vehicles[veh.serial_number] = veh
            updated.append(veh.serial_number)

        for veh in SESSION.vehicles:
            if veh not in updated:
                del SESSION.vehicles[veh]

    def get_vehicles(self):
        return SESSION.vehicles

    def get_vehicles_by_serial(self, serial):
        for vehicle in SESSION.vehicles:
            if vehicle.serial_number == serial:
                return vehicle

        return None

    async def _request(self, method, url, data=None, params=None):
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                resp = await session.get(
                    url=url,
                    data=data,
                    params=params,
                    headers={
                        **HTTP_HEADER,
                        "token": self.token if not self.token is None else "",
                    },
                )
            elif method == "POST":
                resp = await session.post(
                    url=url,
                    data=data,
                    params=params,
                    headers={
                        **HTTP_HEADER,
                        "token": self.token if not self.token is None else "",
                    },
                )
            else:
                raise ValueError("Illegal method")

        resp_json = await resp.json()

        if resp.status >= 500:
            raise NiuServerException(f"HTTP error {resp.status}")
        elif resp.status >= 400:
            raise NiuAPIException(f"HTTP error {resp.status}")
        elif resp.status >= 300:
            raise NiuNetException(f"HTTP error {resp.status}")
        elif resp.status >= 200:
            status = resp_json.get("status")
            if status != 0:
                raise NiuAPIException(
                    "Error {}: {}".format(status, resp_json["desc"]))

        return resp_json


class Vehicle(dict):
    def __init__(self, *arg, **kw):
        super(Vehicle, self).__init__(*arg, **kw)

    @property
    def serial_number(self):
        return self["sn_id"]

    @property
    def firmware_version(self):
        return self["soft_version"]

    @property
    def model(self):
        return self["scooter_type"]

    @property
    def name(self):
        return self["scooter_name"]

    @property
    def odometer(self):
        return self["totalMileage"]

    @property
    def range(self):
        return self["mileage"]

    def soc(self, index=-1):
        bat = self._get_battery(index)

        if len(bat) == 1:
            return bat[0]["batteryCharging"]

        soc = bat[0]["batteryCharging"] + bat[1]["batteryCharging"]

        return soc / 2

    @property
    def charging_time_left(self):
        if self.is_charging:
            left = float(self["leftTime"])
            hours = int(left)
            minutes = (left - hours) * 60

            return datetime.timedelta(hours=hours, minutes=minutes)
        else:
            return datetime.timedelta(0)

    @property
    def battery_count(self):
        return 2 if self["is_double_battery"] == 1 else 1

    def battery_temp(self, index=-1):
        return self._get_battery_param(index, "temperature")

    def battery_temp_desc(self, index=-1):
        return self._get_battery_param(index, "temperatureDesc")

    @property
    def location(self):
        return {
            "lat": self["postion"]["lat"],
            "lon": self["postion"]["lng"],
            "timestamp": self["gpsTimestamp"],
        }

    @property
    def is_charging(self):
        return self["isCharging"] == 1

    @property
    def is_connected(self):
        return self["isConnected"] == 1

    @property
    def is_on(self):
        return self["isAccOn"] == 1

    @property
    def is_locked(self):
        return self["lockStatus"] == 0

    def _get_battery(self, index):

        if index == 0:
            return [self["batteries"]["compartmentA"]]

        if self.battery_count == 2:
            if index == 1:
                return [self["batteries"]["compartmentB"]]

            if index == -1:
                return [
                    self["batteries"]["compartmentA"],
                    self["batteries"]["compartmentB"],
                ]

        return None

    def _get_battery_param(self, index, param):
        bat = self._get_battery(index)

        if len(bat) == 1:
            return bat[0][param]

        return [x[param] for x in self._get_battery(index)]


class NiuNetException(Exception):
    pass


class NiuServerException(Exception):
    pass


class NiuAPIException(Exception):
    pass
