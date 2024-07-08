"""
Dependencies:
    Python: version 3.8.18
    pyside6: version 6.6.2
    pyserial: version 3.5
    pyvisa: version 1.14.1

Classes:
    DeviceSelectionGUI: Creates the GUI for the selection screen. Allows user to select a device that is currently connected via Pyvisa or Pyserial. Users must click the
    corresponding button to display devices via Pyvisa or Pyserial (the two are separated because of code differences in establishing connections).
        Constructor:
            no parameters
        Methods:
            selectIndex() - no parameters; stores selected index and matches it to the device
            wait() - no parameters; constantly passes to simulate waiting, used to solve issue of GUI immediately closing, waits until the user selects a device before closing
            fillSelection() - array of devices (either Pyvisa or Pyserial); connects to and displays the identification of every available device, Pyvisa and Pyserial are separate because of code differences during connection
"""

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QMessageBox, QListWidget
from PySide6.QtCore import QTimer
import serial
import serial.tools.list_ports

import pyvisa
from pyvisa.errors import VisaIOError
import time

class DeviceSelectionGUI:
    def __init__(self):
        self.selected_device = None
        self.selected_type = ""
        self.rm = pyvisa.ResourceManager()
        self.PyVisaIds = list(self.rm.list_resources())
        self.PySerialIds = []
        self.serialMap = {}
        self.allDevices = []
        self.deleteIndex = []

        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        else:
            self.app.quit()
            self.app = QApplication.instance()

        self.main = QWidget()
        self.main.setWindowTitle("Device Selection")
        self.layout = QVBoxLayout()

        self.Lb = QListWidget()
        self.max_length = 0

        for i in range(len(self.PyVisaIds)):
            try:
                device = self.rm.open_resource(self.PyVisaIds[i])
                device.query("*IDN?")
                self.allDevices.append(device)
            except VisaIOError:
                self.deleteIndex.append(i)

        for i in range(len(self.deleteIndex) - 1, -1, -1):
            self.PySerialIds.insert(0, self.PyVisaIds[self.deleteIndex[i]])
            del self.PyVisaIds[self.deleteIndex[i]]

        self.Lb.setMinimumWidth(self.max_length * 8)
        self.layout.addWidget(self.Lb)

        self.btn_show_index = QPushButton("Select Device")
        self.btn_show_index.clicked.connect(self.selectIndex)
        self.layout.addWidget(self.btn_show_index)

        self.btn_select_pyvisa = QPushButton("Show PyVisa Devices")
        self.btn_select_pyvisa.clicked.connect(lambda: self.fillSelection(self.PyVisaIds))
        self.layout.addWidget(self.btn_select_pyvisa)

        self.btn_select_pyserial = QPushButton("Show PySerial Devices")
        self.btn_select_pyserial.clicked.connect(lambda: self.fillSelection(self.PySerialIds))
        self.layout.addWidget(self.btn_select_pyserial)

        self.main.setLayout(self.layout)
        self.main.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.wait)
        self.timer.start(0)
        self.app.exec()
        self.wait()

    def selectIndex(self):
        selected_indices = self.Lb.selectedIndexes()
        if selected_indices:
            selected_index = selected_indices[0].row()
            if self.selected_type == "PyVisa":
                self.selected_device = ["PyVisa", self.PyVisaIds[selected_index]]
            if self.selected_type == "PySerial":
                self.selected_device = ["PySerial", self.serialMap[selected_index][0], self.serialMap[selected_index][1]]
            self.main.close()
        else:
            QMessageBox.warning(self.main, "No Device Selected", "No Device Selected", QMessageBox.Ok)

    def wait(self):
        pass

    def fillSelection(self, array):
        self.max_length = 1
        self.Lb.clear()
        if array == self.PyVisaIds:
            self.selected_type = "PyVisa"
            for i in range(len(array)):
                try:
                    device = self.rm.open_resource(array[i])
                    device_id = device.query("*IDN?")
                    self.Lb.addItem(device_id)
                    self.max_length = max(self.max_length, len(device_id))
                except VisaIOError:
                    continue
        if array == self.PySerialIds:
            self.selected_type = "PySerial"
            BAUD = [4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
            comlist = serial.tools.list_ports.comports()
            connected = [element.device for element in comlist]

            for i, com in enumerate(connected):
                for baud in BAUD:
                    try:
                        device = serial.Serial(com, baud, timeout=1)
                        device.write(b'*IDN?\n')
                        time.sleep(0.1)
                        device_id = device.read_all().decode("utf-8")
                        device.close()
                        if device_id:
                            self.Lb.addItem(device_id)
                            self.max_length = max(self.max_length, len(device_id))
                            self.serialMap[i] = [com, baud]
                            break
                    except Exception as e:
                        print(e)
                        continue