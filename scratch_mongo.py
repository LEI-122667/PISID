import pymongo
from pprint import pprint
uri = "mongodb://root:root@localhost:27018/"
client = pymongo.MongoClient(uri, 2000)
db = client["pisid_maze"]
col = db["sensor_ruido"]
doc = col.find_one()
if doc:
    print("Type of Hour:", type(doc.get("Hour")))
    print("Value of Hour:", doc.get("Hour"))
else:
    print("No docs in sensor_ruido")
