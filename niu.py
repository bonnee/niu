import json
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError as RequestsHTTPError

NIU_LOGIN_URL = "https://account-fk.niu.com"
NIU_API_URL = "https://app-api-fk.niu.com"

HTTP_HEADER = {
    'User-Agent': 'manager/4.1.0 (android; ONEPLUS A6013 9);lang=it-IT;clientIdentifier=Overseas;timezone=Europe/Rome;brand=OnePlus;model=ONEPLUS A6013;osVersion=9;pixels=1080x2261',
    # 'User-Agent': 'lang={};clientIdentifier=Overseas',
    'Content-Type': 'application/x-www-form-urlencoded'
}


class Session:
    username = ""
    password = ""
    lang = ""
    token = ""
    vehicles = ""


SESSION = Session()


class NiuCloud:

    def init(self, username, password, token="", lang="en-US"):
        SESSION.username = username
        SESSION.password = password
        SESSION.token = token
        SESSION.lang = lang

        HTTP_HEADER['User-Agent'] = HTTP_HEADER['User-Agent'].format(lang)

        if username is None or password is None:
            return None
        else:
            if SESSION.token == "":
                self.get_token()

            self.get_vehicles()

        return SESSION.token

    def get_token(self):
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
        if SESSION.username == "" or SESSION.password == "":
            raise NiuAPIException("Can't find username or password")
        if SESSION.token == "":
            self.get_token()

    def get_vehicles(self):
        self.check_access_token()

        vehicles = self._request(
            'GET',
            NIU_API_URL + '/v5/scooter/list')['data']['items']

        SESSION.vehicles = []
        for vehicle in vehicles:
            resp = self._request(
                'GET',
                NIU_API_URL + '/v5/scooter/detail/{}'.format(vehicle['sn_id'])
            )
            SESSION.vehicles.append(resp['data'])

    def get_all_vehicles(self):
        return SESSION.vehicles

    def get_vehicles_by_serial(self, serial):
        for vehicle in SESSION.vehicles:
            if vehicle.sn_id == serial:
                return vehicle

        return None

    def _request(self, method, url, data=None):
        try:
            resp = requests.request(method=method, url=url,
                                    headers={**HTTP_HEADER, 'token': SESSION.token})

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


class NiuNetException(Exception):
    pass


class NiuServerException(Exception):
    pass


class NiuAPIException(Exception):
    pass
