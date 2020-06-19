import sys

from niu import NiuCloud

niu = NiuCloud()

token = ""
if len(sys.argv) > 3:
    token = sys.argv[3]

t = niu.init(sys.argv[1], sys.argv[2], token, "it-IT")

print(niu.get_all_vehicles()[0]['batteries'])


if token == "":
    print(t)
