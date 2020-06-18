import sys

from niu import NiuCloud

niu = NiuCloud()

token = ""
if len(sys.argv) > 1:
    token = sys.argv[1]

t = niu.init("***REMOVED***", "rFgN4RSR7U84tzk", token, "it-IT")

print(niu.get_all_vehicles()[0]['sn_id'])


if token == "":
    print(t)
