#!/usr/bin/env python
# coding: utf-8

# In[20]:


# Imports

import pyvisa
from pyvisa.errors import VisaIOError
from datetime import datetime
import time
# In[21]:


# Variables

list_devices = False # If you want to list devices at start set this to true
NPLC = 60 # NPLC is 30Hz, not 60, not sure why
# It is set to NPLC/2 while taking measurements, so enter 60Hz values for the variable
cycles = 5 # Number of measurements to take


# In[22]:


# Functions

def init():
    """Connects to device"""
    rm = pyvisa.ResourceManager()
    if list_devices:
        print(rm.list_resources())
    DMM = rm.open_resource('GPIB0::22::INSTR')
    DMM.read_termination = '\r'
    DMM.write_termination = '\r'
    DMM.query('ID?')
    return DMM
    
def test(DMM):
    """Tests device connection"""
    DMM.write("RESET")
    DMM.write("TARM HOLD")
    DMM.write("DCV 10")
    DMM.write("NPLC 1")
    DMM.write("AZERO OFF")
    DMM.write("TARM SGL")
    test = DMM.read().strip()
    if "E" in test:
        pass
    else:
        return None
    error = DMM.query("ERR?")
    if error == "0":
        pass
    else:
        return None
    return True

def setup(DMM):
    """Clears the device and tests it before taing measurements"""
    output = DMM.write("TARM HOLD")
    if output == 10:
        pass
    else:
        return None
    DMM.write("PRESET NORM")
    DMM.write("INBUF ON")
    DMM.write("NRDGS 10, AUTO")
    DMM.write("TRIG SGL")
    arr = DMM.read_bytes(10)
    arr = str(arr, encoding='utf-8')
    if " " or "-" in str(arr):
        pass
    else:
        return None
    return True


# In[23]:


# Setup

print("Starting setup.")
print("Initiating device.")
print("Testing device")
DMM = init() # Initiates device
init_test = test(DMM) # Tests device
if init_test:
    print("Initiation successful.")
else:
    print("Error in initiation or test.")
setup_test = setup(DMM) # Prepares device for taking measurements
if setup_test:
    print("Setup successful.")
else:
    print("Error in setup.")


# In[31]:


print("\nStarting measurement process.\n")

finished = False
DMM.write("PRESET NORM") # Clears memory
DMM.write("TARM HOLD")
DMM.write("DCV 1")
DMM.write(f"NPLC {NPLC/2}") # As mentioned above, NPLC is 30Hz not 60Hz, but enter 30Hz values above
DMM.write("MEM FIFO")
DMM.write("TRIG AUTO")
print("Beginning measurements. DO NOT GO ON TO THE NEXT SECTION UNTIL THIS IS COMPLETE.")
now = time.time()
start = time.perf_counter()
DMM.write(f"NRDGS {cycles}, AUTO")
DMM.write("TARM SGL, 1")
while True:
    try:
        DMM.write("RMEM " + str(cycles))
        finished = True
    except VisaIOError:
        pass
    if finished == True:
        end = time.perf_counter()
        time_difference_seconds = end - start
        print(time_difference_seconds)
        interval = time_difference_seconds / cycles
        break


# In[32]:


print("Measurements complete!")
arr, nowarr = [], []
start += now
for i in range(1,cycles+1):
    DMM.write("RMEM " + str(i))
    arr.append(DMM.read())
    print(f"{i},{now}")
    now = datetime.fromtimestamp(start+(interval*i))
    nowvar = now.strftime("%d/%m/%y-%H:%M:%S")
    nowarr.append(nowvar)
print(arr)
print(nowarr)
with open("output.csv", "w") as output:
    for now_line, arr_line in zip(nowarr, arr):
        output.write(str(now_line))
        output.write(",")
        output.write(str(arr_line).strip())
        output.write("\n")