import sys

from niu import NiuCloud


token = ""
if len(sys.argv) > 3:
    token = sys.argv[3]

niu = NiuCloud(sys.argv[1], sys.argv[2], token, "it-IT")

niu.connect()
vehicles = niu.get_vehicles()

print("Found {} vehicles:".format(len(vehicles)))
for veh in vehicles:
    print("\tSerial:\t\t{}".format(veh.get_serial()))
    print("\tModel:\t\t{}".format(veh.get_model()))
    print("\tName:\t\t{}".format(veh.get_name()))

    print("\tSoC:\t\t{}% [{}%, {}%]".format(
        veh.get_soc(), veh.get_soc(0), veh.get_soc(1))
    )
    print("\tCharging:\t{}".format(veh.is_charging()))

    print("\tTemps:\t\t{}".format(veh.get_battery_temp()))
    print("\tLocation:\t{}".format(veh.get_location()))

if token == "":
    pass
    #print("\nConnection token:\t{}".format(t))
