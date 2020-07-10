import json
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError as RequestsHTTPError

NIU_LOGIN_URL = "https://account-fk.niu.com"
NIU_API_URL = "https://app-api-fk.niu.com"

HTTP_HEADER = {
    'User-Agent': 'manager/4.1.0 (android; NoPhone 1 9);lang=it-IT;clientIdentifier=Overseas;timezone=Europe/Rome;brand=NoPhone 1;model=NoPhone 1;osVersion=9;pixels=1080x1920',
    # 'User-Agent': 'lang={};clientIdentifier=Overseas',
    'Content-Type': 'application/x-www-form-urlencoded'
}


class Session:
    username = ""
    password = ""
    lang = ""
    token = ""
    vehicles = []


SESSION = Session()


class NiuCloud:

    def __init__(self, username=None, password=None, token=None, lang="en-US"):
        SESSION.username = username
        SESSION.password = password
        SESSION.token = token
        SESSION.lang = lang

        HTTP_HEADER['User-Agent'] = HTTP_HEADER['User-Agent'].format(lang)

    def connect(self):
        if SESSION.token == None:
            if SESSION.username is None or SESSION.password is None:
                return None

            self.get_new_token()

        self.update_vehicles()

    def get_token(self):
        return SESSION.token

    def get_new_token(self):
        if SESSION.username == "" or SESSION.password == "":
            raise NiuAPIException("Can't find username or password")

        try:
            resp = requests.post(
                NIU_LOGIN_URL + "/appv2/login",
                headers=HTTP_HEADER,
                data={
                    'account': SESSION.username,
                    'password': SESSION.password
                })
            resp.raise_for_status()

        except RequestsConnectionError as ex:
            raise NiuNetException from ex
        except RequestsHTTPError as ex:
            if resp.status_code >= 500:
                raise NiuServerException from ex

        resp_json = resp.json()

        status = resp_json.get("status")
        if (status != 0):
            raise NiuAPIException(
                "Error {}: {}".format(status, resp_json['desc']))

        SESSION.token = resp_json['data']['token']

    def check_access_token(self):
        if SESSION.token == "":
            self.get_new_token()

    def update_vehicles(self):
        self.check_access_token()

        vehicles = self._request(
            'GET',
            NIU_API_URL + '/v5/scooter/list'
        )['data']['items']

        SESSION.vehicles = []

        for vehicle in vehicles:
            veh = Vehicle()
            SESSION.vehicles.append(veh)

            veh.update(vehicle)

            # Get general details
            resp = self._request(
                'GET',
                NIU_API_URL + '/v5/scooter/detail/{}'.format(veh.get_serial())
            )
            veh.update(resp['data'])

            # Get vehicle status
            resp = self._request(
                'GET',
                NIU_API_URL + '/v3/motor_data/index_info',
                params={'sn': veh.get_serial()}
            )
            veh.update(resp['data'])

            # Get batteries status
            resp = self._request(
                'GET',
                NIU_API_URL + '/v3/motor_data/battery_info',
                params={'sn': veh.get_serial()}
            )
            veh.update(resp['data'])

    def get_vehicles(self):
        return SESSION.vehicles

    def get_vehicles_by_serial(self, serial):
        for vehicle in SESSION.vehicles:
            if vehicle.get_serial() == serial:
                return vehicle

        return None

    def _request(self, method, url, data=None, params=None):
        try:
            resp = requests.request(
                method=method, url=url,
                data=data, params=params,
                headers={**HTTP_HEADER, 'token': SESSION.token}
            )

            resp.raise_for_status()

        except RequestsConnectionError as ex:
            raise NiuNetException from ex
        except RequestsHTTPError as ex:
            if resp.status_code >= 500:
                raise NiuServerException from ex

        resp_json = resp.json()

        status = resp_json.get("status")
        if (status != 0):
            raise NiuAPIException(
                "Error {}: {}".format(status, resp_json['desc']))

        return resp_json


class Vehicle(dict):
    def __init__(self, *arg, **kw):
        super(Vehicle, self).__init__(*arg, **kw)

    def get_serial(self):
        return self['sn_id']

    def get_model(self):
        return self['scooter_type']

    def get_name(self):
        return self['scooter_name']

    def get_soc(self, index=-1):
        bat = self._get_battery(index)

        if len(bat) == 1:
            return bat[0]['batteryCharging']

        soc = bat[0]['batteryCharging'] + bat[1]['batteryCharging']

        return soc / 2

    def is_charging(self):
        return self['isCharging'] == 1

    def get_battery_temp(self, index=-1):
        bat = self._get_battery(index)

        if (len(bat) == 1):
            return bat[0]['temperature']

        return [x['temperature'] for x in self._get_battery(index)]

    def get_location(self):
        return {
            'lat': self['postion']['lat'],
            'lon': self['postion']['lng'],
            'timestamp': self['gpsTimestamp']
        }

    def _get_battery(self, index):

        if index == 0:
            return [self['batteries']['compartmentA']]

        if self['is_double_battery']:
            if index == 1:
                return [self['batteries']['compartmentB']]

            if index == -1:
                return [self['batteries']['compartmentA'], self['batteries']['compartmentB']]

        return None


class NiuNetException(Exception):
    pass


class NiuServerException(Exception):
    pass


class NiuAPIException(Exception):
    pass
