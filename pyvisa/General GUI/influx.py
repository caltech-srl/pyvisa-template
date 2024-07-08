"""
Dependencies:
    Python: version 3.8.18
    influxdb-client: version 1.43.0

Classes:
    InfluxClient: Initializes an InfluxDB client to write data
        Constructor:
            token: security token obtained from Influx
            org: set organization on Influx
            bucket: bucket to write data to in Influx
        Methods:
            write_data() - data to write; writes data to InfluxDB based on the bucket in the constructor, logs successful and failed writes
"""

#sleep configured in GUI to enable adjustment of frequency during recording
#when sleep configured here, you have to stop recording, then change the frequency

from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient
#from time import sleep
import logging
from influxdb_client import InfluxDBClient


class InfluxClient:
    def __init__(self, token, org, bucket): 
        self._org = org 
        self._bucket = bucket
        self._client = InfluxDBClient(url="http://bragi.caltech.edu:8086", token=token)

    def write_data(self, data, write_option=SYNCHRONOUS):
        write_api = self._client.write_api(write_option)
        try:
            write_api.write(self._bucket, self._org, data, write_precision='s')
            logging.info('Data written successfully')
        except Exception as e:
            logging.error(f'Failed to write data: {e}')
            #sleep(1000)