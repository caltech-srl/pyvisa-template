from datetime import datetime
from influxdb_client.client.write_api import SYNCHRONOUS
from assets.connect import Connect
from assets.functions import InfluxClient
from assets.voltage import Voltage
from time import sleep

token, org, bucket = Connect()

IC = InfluxClient(token, org, bucket)
value=0.1

for i in range(1,61):
    time=int(datetime.now().timestamp())
    voltage = Voltage()
    IC.write_data(IC.write_data([f"3458a,multimeter=3458a voltage={voltage} {time}"]), write_option=SYNCHRONOUS)
    IC.write_data(IC.write_data([f"alt,multimeter=3458a voltage={5-voltage} {time}"]), write_option=SYNCHRONOUS)
    IC.write_data(IC.write_data([f"plus3,multimeter=3458a voltage={voltage+3} {time}"]), write_option=SYNCHRONOUS)
    IC.write_data(IC.write_data([f"climb,multimeter=3458a voltage={value} {time}"]), write_option=SYNCHRONOUS)
    sleep(1)
    value += .1
    print(f"{i}, {time}, {voltage:.2f}")