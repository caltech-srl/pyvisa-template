"""
Starts Screen for GUIs

Dependencies:
    Python: version 3.8.18
    pyvisa: version 1.14.1
    pyside6: version 6.6.2
    pyserial: version 3.5
    all GUIs that have been made

No Classes

Methods:
    sample() - all parameters; description

    GUI_start() - no parameters, creates the selection GUI, Pyvisa and Pyserial devices are separated and have designated buttons to display
"""

# PyVisa imports
import pyvisa
import time

#Pyside6 imports
from PySide6.QtWidgets import QApplication

# PySerial imports
import serial
import serial.tools.list_ports
import sys

#Python Scripts
from selection import DeviceSelectionGUI
from E36312A import GUI_E36312A

def GUI_start():
    gui = DeviceSelectionGUI()
    selected_device = gui.selected_device
    if not selected_device:
        sys.exit()

    rm = pyvisa.ResourceManager()
    if selected_device[0] == "PyVisa":
        my_device = rm.open_resource(selected_device[1])
        id = my_device.query("*IDN?").split(",")
    if selected_device[0] == "PySerial":
        my_device = serial.Serial(selected_device[1], selected_device[2], timeout=1)
        my_device.write(b'*IDN?\n')
        time.sleep(0.1)
        id = my_device.read_all().decode("utf-8").split(",")

    class_name = f"GUI_{id[1]}"
    if hasattr(sys.modules[__name__], class_name):
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            else:
                app.quit()
                app = QApplication.instance()

            main_window = globals()[class_name](my_device)
            main_window.show()
            app.exec()
        except Exception as e:
            app.quit()
            my_device.close()
            sys.exit()

GUI_start()