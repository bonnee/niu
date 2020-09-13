#!/usr/bin/python

import sys
import asyncio
from niu import NiuCloud


async def do(usr, pwd, token):
    niu = NiuCloud(username=usr, password=pwd, token=token, lang="it-IT")
    token = await niu.connect()
    await niu.update_vehicles()
    vehicles = niu.get_vehicles()

    print("Found {} vehicles:".format(len(vehicles)))
    for sn, veh in niu.get_vehicles().items():
        print("\tSerial:\t\t{}".format(veh.serial_number))
        print("\tFirmware:\t{}".format(veh.firmware_version))
        print("\tModel:\t\t{}".format(veh.model))
        print("\tName:\t\t{}".format(veh.name))
        print("\tOdometer:\t{} Km".format(veh.odometer))
        print("\tRange:\t\t{} Km".format(veh.range))

        print(
            "\tSoC:\t\t{}% {}".format(
                veh.soc(),
                [veh.soc(x) for x in range(0, veh.battery_count)],
            )
        )
        print(f"\tConnected:\t{veh.is_connected}")
        print(f"\tPower:\t\t{veh.is_on}")
        print(
            f"\tCharging:\t{veh.is_charging} ({veh.charging_time_left} left)")
        print(f"\tLocked:\t\t{veh.is_locked}")

        descs = veh.battery_temp_desc
        temps = veh.battery_temp

        print("\tTemps:\t\t", end="")
        for i, temp in enumerate(temps):
            print(f"{temps[i]} °C ({descs[i]}), ", end="")
            print()  # newline

        print("\tLocation:\t{}".format(veh.location))

    print("\nConnection token:\t{}".format(token))


if __name__ == "__main__":
    token = ""
    if len(sys.argv) > 3:
        token = sys.argv[3]

    usr = sys.argv[1]
    pwd = sys.argv[2]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(do(usr, pwd, token))
    loop.close()
