#!/usr/bin/python

import sys

from niu import NiuCloud

token = ""
if len(sys.argv) > 3:
    token = sys.argv[3]

usr = sys.argv[1]
pwd = sys.argv[2]

niu = NiuCloud(token=token, lang="it-IT")

niu.connect()
vehicles = niu.get_vehicles()

print("Found {} vehicles:".format(len(vehicles)))
for veh in vehicles:
    print("\tSerial:\t\t{}".format(veh.get_serial()))
    print("\tFirmware:\t{}".format(veh.get_firmware()))
    print("\tModel:\t\t{}".format(veh.get_model()))
    print("\tName:\t\t{}".format(veh.get_name()))
    print("\tOdometer:\t{} Km".format(veh.get_odometer()))
    print("\tRange:\t\t{} Km".format(veh.get_range()))

    print(
        "\tSoC:\t\t{}% {}".format(
            veh.get_soc(), [veh.get_soc(x) for x in range(0, veh.get_battery_count())]
        )
    )
    print(f"\tConnected:\t{veh.is_connected()}")
    print(f"\tPower:\t\t{veh.is_on()}")
    print(f"\tCharging:\t{veh.is_charging()} ({veh.get_charging_left()} left)")
    print(f"\tLocked:\t\t{veh.is_locked()}")

    descs = veh.get_battery_temp_desc()
    temps = veh.get_battery_temp()

    print("\tTemps:\t\t", end="")
    for i, temp in enumerate(temps):
        print(f"{temps[i]} °C ({descs[i]}), ", end="")
    print()  # newline

    print("\tLocation:\t{}".format(veh.get_location()))

if token == "":
    pass
    print("\nConnection token:\t{}".format(t))
