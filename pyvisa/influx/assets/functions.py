from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from influxdb_client import InfluxDBClient

class InfluxClient:
    def __init__(self,token,org,bucket): 
        self._org=org 
        self._bucket = bucket
        self._client = InfluxDBClient(url="http://bragi.caltech.edu:8086", token=token)

    def write_data(self,data,write_option=SYNCHRONOUS):
        write_api = self._client.write_api(write_option)
        write_api.write(self._bucket, self._org , data,write_precision='s')