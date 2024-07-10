"""
Dependencies:
    Python: version 3.8.18
    pyvisa: version 1.14.1
    python-dateutil: version 2.8.2
    python-dotenv: version 1.0.1
    influxdb-client: version 1.43.0
    pyside6: version 6.6.2


Classes:
    E36312A_Controls: holds functions that controls the power source
        Constructor: 
            all parameters
            DPS: reference to the connected Digital Power Source
        Methods:
            sample() - all parameters; description

            test() - no parameters; tests the output channels and data logger, resets Power Source to DEFAULT SETTINGS, briefly turns all output channels on
            turnOn() - reference to power source, channel number; turns on the specified channel
            turnOff() - reference to power source, channel number; turns off the specified channel
            turnAllOn() - reference to power source; turns all channels on
            turnAllOff() - reference to power source; turns all channels off
            findVoltageRange() - reference to power source, channel number; returns the minimum and maximum voltage of the specified channel
            findCurrentRange() - reference to power source, channel number; returns the minimum and maximum current limit of the specified channel
            setVoltage() - reference to power source, channel number, voltage; sets the voltage of the specified channel to the specified voltage, if it is within the alotted range
            setCurrentLimit() - reference to power source, channel number, current limit; sets the current limit of the specified channel to the specified current limit, if it is within the alotted range
            getCurrentLimit() - reference to power source, channel number; returns the set current limit
            getSetVoltage() - reference to power source, channel number; returns the set voltage
            getCurrent() - reference to power source, channel number; returns the output current limit
            getVoltage() - reference to power source, channel number; returns the output voltage
            enableDlogVoltage() - reference to power source, channel number; enables the voltage for the specified channel on the data logger
            disableDlogVoltage() - reference to power source, channel number; disables the voltage for the specified channel on the data logger
            enableDlogCurrent() - reference to power source, channel number; enables the current for the specified channel on the data logger
            disableDlogCurrent() - reference to power source, channel number; disables the current for the specified channel on the data logger
            setDlogTime() - reference to power source, time in seconds; sets the duration of time for data logger to record
            writeCommand() - reference to power source, command; queries the power source with the specified command
            changeOperationMode() - reference to power source, mode of operation; changes the operation mode of channel 3 to the specified mode

    GUI_E36312A: Creates the GUI for the power source
        Constructor:
            all parameters
            DPS: reference to the connected Digital Power Source
        Methods:
            sample() - all parameters; description

            createChannel() - channel number; creates the interface for one output channel, with the correct voltage and current limit ranges
            toggleButton() - channel number, reference to the button; turns the specific channel off, updates the appearance of the button
            toggleAllChannelsOn() - no parameters; turns all channels on, updates button texts
            toggleAllChannelsOff() - no parameters; turns all channels off, updates button texts
            readVoltageEntry() - channel number, reference to voltage entry text box; sets the voltage of the specified channel to the specified voltage, updates set voltage label
            readCurrentEntry() - channel number, reference to current limit entry text box; sets the current limit of the specified channel to the specified current limit, updates set current limit label
            updateVoltageCurrent() - channel number, reference to voltage label, reference to current label; updates the voltage and current readings as measured by the power source
            addTerminal() - no parameters; createsthe interface for the terminal
            sendTerminalCommand() - no parameters; queries the power source with the inputted command and displays the response
            createNotesBox() - no parameters; creates the interface for the notes
            importTextFile() - no parameters; displays the saved notes from previous sessions
            saveNotes() - no parameters; saves the notes in the textbox to a text file
            startRecording() - reference to status label; starts recording data at specified frequency, updates status label
            stopRecording() - reference to status label; stops recording data, updates status label
            setRecordingDelay() - time delay, reference to frequency label, reference to frequency entry box; updates the frequency of measurements, updates the label
            record() - reference to power source; queries all three channels of the power source and writes voltage and current to InfluxDB if the channel is turned on
            addRecording() - reference to bucket label, reference to recording status label; creates the interface for the data recorder
            displayBuckets() - no parameters; lists all available buckets in InfluxDB
            selectBucket() - reference to bucket label; updates the selected bucket, updates bucket label
            createBucket() - reference to bucket entry box; creates new InfluxDB bucket, refreshes bucket list
            syncPowerSupply() - reference to power source, reference to on/off button, reference to channel number, reference to voltage label, reference to current label; syncs the status of each channel on the GUI with the power source
            syncOutputChannel() - reference to power source, reference to the channel 3 widget, reference to the timer updating the status of channel 3; Synchronizes channel 3 with operation mode (independent, series, parallel), resets timers used to update channel status to avoid runtime errors
            syncOutputChannel2() - reference to power source, reference to the channel 3 widget; same as above but for when channel 3 is in series or in parallel, without reference to timer because it does not exist
            addChannel3Status() - no parameters; creates interface for changing output mode of channel 3 (Independent, Series, Parallel)
            
    Note: Code that displays the output voltage and current is disabled because it causes significant lag when running.
    Note: It is recommended that the power source be fully configured before user starts recording data as it causes significant lag.
"""


# PyVisa imports
from pyvisa.errors import VisaIOError
from datetime import datetime
from statistics import mean

#Influx imports
import os
from dotenv import load_dotenv
from influxdb_client import BucketRetentionRules, BucketsApi
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient, BucketsApi, BucketRetentionRules

#Pyside6 imports
from PySide6.QtWidgets import QMainWindow, QLabel, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QListWidget, QTextEdit
from PySide6.QtCore import QTimer

import csv

#Python Scripts
from influx import InfluxClient

# Functions
class E36312A_Controls:
    
    def test(self, DPS):
        """Tests device connection"""
        DPS.read_termination = '\n'
        DPS.write_termination = '\n'
        DPS.channels = 3
        DPS.powertest = 13
        DPS.datalog = 30
        DPS.write("*CLS")
        DPS.write("*RST")
        powertest = []
        for state in ['1', '0']:
            for channel in range(DPS.channels):
                powertest.append(DPS.write(f"OUTP {state}, (@{channel+1})"))
        if (not mean(powertest) == DPS.powertest):
            print("Power Test Failed")
            return None
    
        datalog = []
        for state in ['1', '0']:
            for type in ['VOLT', 'CURR']:
                datalog.append(DPS.write(f"SENS:DLOG:FUNC:{type} {state}, (@1:3)"))
        if (not mean(datalog) == DPS.datalog):
            print("Data Logger Test Failed")
            return None
        return True
            
    def turnOn(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
        else:
            DPS.write(f"OUTP 1, (@{ch})")
    
    def turnOff(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
        else:
            DPS.write(f"OUTP 0, (@{ch})")

    def turnAllOn(self, DPS, chlist):
        for ch in chlist:
            DPS.write(f"OUTP 1, (@{ch})")

    def turnAllOff(self, DPS, chlist):
        for ch in chlist:
            DPS.write(f"OUTP 0, (@{ch})")

    def findVoltageRange(self, DPS, ch, paired):
        maximum = 0
        if (ch == 1):  
            maximum = min(float(DPS.query(f"VOLT:PROT? (@{ch})")), 6.18)
        elif (ch == 2):
            if (paired == "OFF\n"):
                maximum = min(float(DPS.query(f"VOLT:PROT? (@{ch})")), 25.75)
            elif (paired == "SER\n"):
                maximum = min(float(DPS.query(f"VOLT:PROT? (@{ch})")), 50)
            elif (paired == "PAR\n"):
                maximum = min(float(DPS.query(f"VOLT:PROT? (@{ch})")), 25)
        elif (ch == 3):
            if (paired == "OFF\n"):
                maximum = min(float(DPS.query(f"VOLT:PROT? (@{ch})")), 25.75)
        return 0, maximum

    def findCurrentRange(self, ch, paired):
        if (ch == 1):
            maximum = 5.15
        else:
            if (paired == "PAR\n"):
                maximum = 2.06
            else:
                maximum = 1.03
        return 0.001, maximum
    
    def setVoltage(self, DPS, ch, voltage, paired):
        range = self.findVoltageRange(DPS, ch, paired)
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
            return -1
        elif voltage > range[1] or voltage < range[0]:
            #print("Voltage Out of Range")
            return -2
        else:
            DPS.write(f"VOLT {voltage}, (@{ch})")
            return 1

    def setCurrentLimit(self, DPS, ch, current):
        range = self.findCurrentRange(DPS, ch)
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
            return -1
        elif current > range[1] or current < range[0]:
            #print("Current Out of Range")
            return -2
        else:
            DPS.write(f"CURR {current}, (@{ch})")
            return 1
    
    def getCurrentLimit(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
            return None
        else:
            current = DPS.query(f"SOUR:CURR? (@{ch})")
            return current
    
    def getSetVoltage(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
            return None
        else:
            voltage = DPS.query(f"SOUR:VOLT? (@{ch})")
            return voltage
    
    def getCurrent(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
            return None
        else:
            current = DPS.query(f"MEAS:CURR:DC? (@{ch})")
            return current
    
    def getVoltage(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
            return None
        else:
            voltage = DPS.query(f"MEAS:VOLT:DC? (@{ch})")
            return voltage
    
    def enableDlogVoltage(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
        else:
            DPS.write(f"SENS:DLOG:FUNC:VOLT 1, (@{ch})")
    
    def disableDlogVoltage(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
        else:
            DPS.write(f"SENS:DLOG:FUNC:VOLT 0, (@{ch})")
    
    def enableDlogCurrent(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
        else:
            DPS.write(f"SENS:DLOG:FUNC:CURR 1, (@{ch})")
    
    def disableDlogCurrent(self, DPS, ch):
        chlist=[1,2,3]
        if int(ch) not in chlist:
            print("Invalid Channel")
        else:
            DPS.write(f"SENS:DLOG:FUNC:CURR 0, (@{ch})")
    
    def setDlogTime(self, DPS, time):
        DPS.write(f"SENS:DLOG:TIME {time}")
    
    def startDlog(self, DPS, file):
        DPS.write(f"INIT:DLOG 'External:/{file}.csv'")

    def writeCommand(self, DPS, command):
        try:
            response = DPS.query(command)
            return response
        except VisaIOError:
            return "Invalid Command"
        
    def changeOperationMode(self, DPS, mode):
        DPS.write(f"OUTP:PAIR {mode}")
        

class GUI_E36312A(QMainWindow):
    def __init__(self, DPS, parent=None): 
        global channels
        global x
        global allButtons
        global upload_timer
        global buckets
        global bucketList
        global bucketNames
        global selectedBucket
        global frequency
        global token
        global org
        global buckets_api
        global terminal_layout
        global control_layout
        global recording_layout
        global channel_layout
        global paired
        global channel_timer

        load_dotenv()
        token = os.getenv('TOKEN')
        org = os.getenv('ORG')

        self.client = InfluxDBClient(url="http://bragi.caltech.edu:8086", token=token, org=org)
        
        # Initialize BucketsApi with the client
        buckets_api = BucketsApi(self.client)

        frequency = 2.0
        selectedBucket = "None"
        bucketList = buckets_api.find_buckets().buckets
        bucketNames = []
        buckets = QListWidget()
        allButtons = []
        x = E36312A_Controls()
        super().__init__(parent)
        self.DPS = DPS
        #This commented code runs a test on the device. The test resets the device.
        # init_test = x.test(DPS) # Tests device
        # if init_test:
        #     pass
        # else:
        #     print("Error in initiation or test")

        channels = [1, 2, 3]
        paired = DPS.query("OUTP:PAIR?")
        if (paired != "OFF\n"):
            channels = [1, 2]

        self.setWindowTitle("E36312A GUI")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QHBoxLayout(self.central_widget)
        
        control_layout = QVBoxLayout()
        recording_layout = QVBoxLayout()

        channel_layout = QHBoxLayout()

        self.outputLabel = QLabel("Output Channels")
        control_layout.addWidget(self.outputLabel)

        channel_timer = QTimer(control_layout)

        self.createChannel(1)
        self.createChannel(2)
        self.createChannel(3)

        control_layout.addLayout(channel_layout)

        self.addChannel3Status()

        self.allOnButton = QPushButton("Turn All On", clicked=lambda: self.toggleAllChannelsOn())
        control_layout.addWidget(self.allOnButton)

        self.allOffButton = QPushButton("Turn All Off", clicked=lambda: self.toggleAllChannelsOff())
        control_layout.addWidget(self.allOffButton)


        terminal_layout = QVBoxLayout()

        # Add Terminal section
        self.addTerminal()

        self.createNotesBox()
        self.importTextFile()
        self.notes_edit.textChanged.connect(self.saveNotes)
        control_layout.addLayout(terminal_layout)

        self.recordLabel = QLabel("Record to InfluxDB and Grafana")
        recording_layout.addWidget(self.recordLabel)

        self.bucketLabel = QLabel("Selected Bucket: None")
        recording_layout.addWidget(self.bucketLabel)

        self.currentFrequencyLabel = QLabel(f"Frequency of Measurements: {frequency}s")
        recording_layout.addWidget(self.currentFrequencyLabel)

        self.isRecording = QLabel("Status: Recording Stopped")
        recording_layout.addWidget(self.isRecording)
        
        self.addRecording(self.bucketLabel, self.isRecording)

        main_layout.addLayout(control_layout)
        main_layout.addLayout(recording_layout)     

        upload_timer = QTimer(self)
        upload_timer.timeout.connect(lambda: self.record(self.DPS))


    
    def createChannel(self, ch):
        global channel_timer
        if (paired != "OFF\n" and ch == 3):
            self.layoutC = QVBoxLayout()
            channel_label = QLabel(f"Channel {ch}")
            self.layoutC.addWidget(channel_label)
            self.stat = ""
            if (paired == "SER\n"):
                self.stat = "In Series with Channel 2"
            elif (paired == "PAR\n"):
                self.stat = "In Parallel with Channel 2"
            self.status_label = QLabel(self.stat)
            self.layoutC.addWidget(self.status_label)
            self.widget = QWidget()
            self.widget.setLayout(self.layoutC)
            self.widget.setStyleSheet("background-color: rgba(0, 0, 255, 64);")
            channel_layout.addWidget(self.widget)

            if channel_timer.isActive():
                channel_timer.stop()
                del channel_timer

            channel_timer = QTimer(control_layout)
            channel_timer.timeout.connect(lambda: self.syncOutputChannel2(self.DPS, self.widget))
            channel_timer.start(1000)

        else:
            global allButtons
            self.layoutC = QVBoxLayout()
            channel_label = QLabel(f"Channel {ch}")
            self.layoutC.addWidget(channel_label)

            setVoltageLabel = QLabel("Voltage: 0.000V")
            self.layoutC.addWidget(setVoltageLabel)

            if (ch == 1):
                setCurrentLimitLabel = QLabel("Current: 5.000A")
            else:
                setCurrentLimitLabel = QLabel("Current: 1.000A")
            self.layoutC.addWidget(setCurrentLimitLabel)
            button = QPushButton("OFF", clicked=lambda: self.toggleButton(ch, button))
            button.setStyleSheet("background-color: red")
            self.layoutC.addWidget(button)

            allButtons.append(button)
            voltage_range = x.findVoltageRange(self.DPS, ch, paired)
            voltage_label = QLabel("Set Voltage")
            self.layoutC.addWidget(voltage_label)

            voltage_entry = QLineEdit()
            hint_voltage = f"{voltage_range[0]}V - {voltage_range[1]}V"
            voltage_entry.setPlaceholderText(hint_voltage)
            voltage_entry.setStyleSheet("color: black")
            voltage_entry.setStyleSheet("background-color: white")
            voltage_entry.installEventFilter(self)  # To handle placeholder text behavior
            self.layoutC.addWidget(voltage_entry)

            voltage_button = QPushButton("Set Voltage", clicked=lambda: self.readVoltageEntry(ch, voltage_entry))
            voltage_button.setStyleSheet("background-color: white")
            self.layoutC.addWidget(voltage_button)

            current_range = x.findCurrentRange(ch, paired)
            current_label = QLabel("Set Current Limit")
            self.layoutC.addWidget(current_label)

            current_entry = QLineEdit()
            hint_current = f"{current_range[0]}A - {current_range[1]}A"
            current_entry.setPlaceholderText(hint_current)
            current_entry.setStyleSheet("color: black")
            current_entry.setStyleSheet("background-color: white")
            current_entry.installEventFilter(self)  # To handle placeholder text behavior
            self.layoutC.addWidget(current_entry)

            current_button = QPushButton("Set Current Limit", clicked=lambda: self.readCurrentEntry(ch, current_entry))
            current_button.setStyleSheet("background-color: white")

            self.layoutC.addWidget(current_button)

            # To display and update voltage and current readings:
            display_voltage = QLabel()
            self.layoutC.addWidget(display_voltage)

            display_current = QLabel()
            self.layoutC.addWidget(display_current)

            #This code displays the actual outputs of each channel; disabled because it causes significant lag
            # update_timer = QTimer(self)
            # update_timer.timeout.connect(lambda: self.updateVoltageCurrent(ch, display_voltage, display_current))
            # update_timer.start(1000)

            self.widget = QWidget()
            self.widget.setLayout(self.layoutC)
            if (ch == 1):
                self.widget.setStyleSheet("background-color: rgba(255, 255, 0, 64);")
            if (ch == 2):
                self.widget.setStyleSheet("background-color: rgba(0, 128, 0, 64);")
            if (ch == 3):
                self.widget.setStyleSheet("background-color: rgba(0, 0, 255, 64);")


            channel_layout.addWidget(self.widget)

            update_timer = QTimer(control_layout)
            update_timer.timeout.connect(lambda: self.syncPowerSupply(self.DPS, button, ch, setVoltageLabel, setCurrentLimitLabel))
            update_timer.start(1000)

            if channel_timer.isActive():
                channel_timer.stop()
                del channel_timer
            
            channel_timer = QTimer(control_layout)
            channel_timer.timeout.connect(lambda: self.syncOutputChannel(self.DPS, self.widget, update_timer))
            channel_timer.start(1000)

    def toggleButton(self, ch, button):
        if button.text() == 'OFF':
            x.turnOn(self.DPS, ch)
            button.setText('ON')
            button.setStyleSheet("background-color: green")
        else:
            x.turnOff(self.DPS, ch)
            button.setText('OFF')
            button.setStyleSheet("background-color: red")

    def toggleAllChannelsOn(self):
        global x

        x.turnAllOn(self.DPS, channels)
        for i in channels:  # Assuming you have 3 channels
            allButtons[i - 1].setText("ON")
            allButtons[i - 1].setStyleSheet("background-color: green")

    def toggleAllChannelsOff(self):
        x.turnAllOff(self.DPS, channels)
        for i in channels:  # Assuming you have 3 channels
            allButtons[i - 1].setText("OFF")
            allButtons[i - 1].setStyleSheet("background-color: red")
            
    def readVoltageEntry(self, ch, voltage_entry):
        text = voltage_entry.text()
        voltage_entry.clear()
        if text == "" or text.startswith("Set Voltage"):
            QMessageBox.warning(self, "Warning", "No Input", QMessageBox.Ok)
            return
        try:
            voltage = float(text)
            result = x.setVoltage(self.DPS, ch, voltage, paired)
            if result == -2:
                QMessageBox.warning(self, "Warning", "Voltage Entered Out Of Range", QMessageBox.Ok)
        except ValueError:
            pass

    def readCurrentEntry(self, ch, current_entry):
        text = current_entry.text()
        current_entry.clear()
        if text == "" or text.startswith("Set Current Limit"):
            QMessageBox.warning(self, "Warning", "No Input", QMessageBox.Ok)
            return
        try:
            current = float(text)
            result = x.setCurrentLimit(self.DPS, ch, current)
            if result == -2:
                QMessageBox.warning(self, "Warning", "Current Entered Out Of Range", QMessageBox.Ok)
        except ValueError:
            pass

    def updateVoltageCurrent(self, ch, display_voltage, display_current):
        voltage = float(x.getVoltage(self.DPS, ch))
        display_voltage.setText(f"{voltage} V")

        current = float(x.getCurrent(self.DPS, ch))
        display_current.setText(f"{current} A")

        csv_file = f'E36312A_channel{ch}.csv'
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            row = (datetime.datetime.now(), voltage, current, voltage*current)
            writer.writerow(row)

    def addTerminal(self):
        self.layoutT = QVBoxLayout()
        terminal_label = QLabel("Terminal")
        self.layoutT.addWidget(terminal_label)

        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Enter command")
        self.terminal_input.setStyleSheet("color: black")
        self.layoutT.addWidget(self.terminal_input)

        terminal_button = QPushButton("Send Command", clicked=self.sendTerminalCommand)
        self.layoutT.addWidget(terminal_button)

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.layoutT.addWidget(self.terminal_output)
        terminal_layout.addLayout(self.layoutT)

    def sendTerminalCommand(self):
        command = self.terminal_input.text()
        self.terminal_input.clear()
        if command:
            response = x.writeCommand(self.DPS, command)
            self.terminal_output.append(f"Command: {command}\nResponse: {response}\n")

    
    def createNotesBox(self):
        self.layoutN = QVBoxLayout()
        notes_label = QLabel("Notes")
        self.layoutN.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.layoutN.addWidget(self.notes_edit)
        terminal_layout.addLayout(self.layoutN)

    def importTextFile(self):
        file_path = "C:\\Users\\spx_v\\Downloads\\PyVisa\\GUI_General\\E36312A_Notes.txt"

        try:
            with open(file_path, 'r') as file:
                text = file.read()
            self.notes_edit.setPlainText(text)
        except FileNotFoundError:
            QMessageBox.warning(self, "File Not Found", f"File '{file_path}' not found.", QMessageBox.Ok)

    def saveNotes(self):
        file_path = "C:\\Users\\spx_v\\Downloads\\PyVisa\\GUI_General\\E36312A_Notes.txt"
        try:
            with open(file_path, 'w') as file:
                text = self.notes_edit.toPlainText()
                file.write(text)
        except IOError:
            QMessageBox.warning(self, "Error", f"Failed to save file '{file_path}'", QMessageBox.Ok)

    def startRecording(self, label):
        global upload_timer
        if (selectedBucket == "None"):
            QMessageBox.warning(label, "No Bucket Selected", "No Bucket Selected", QMessageBox.Ok)
        else:
            if not upload_timer.isActive():
                upload_timer.start(frequency * 1000)
                label.setText("Status: Recording Started")

        
    def stopRecording(self, label):
        global upload_timer
        upload_timer.stop()
        label.setText("Status: Recording Stopped")

    def setRecordingDelay(self, time, label, textbox):
        global frequency
        try:
            frequency = float(time)
            label.setText(f"Frequency of Measurements: {frequency}s")
            textbox.clear()
            if (frequency < 2):
                QMessageBox.warning(self, "Warning", "Frequency under 2 seconds may result in inconsistent measurements due to execution time of the code", QMessageBox.Ok)
            if upload_timer.isActive():
                upload_timer.stop()
                upload_timer.start(int(frequency * 1000))
            else:
                upload_timer.stop()
        except ValueError as e:
            QMessageBox.warning(self, "Error", "Invalid frequency value", QMessageBox.Ok)

            
    def record(self, DPS):
        IC = InfluxClient(token, org, selectedBucket)
        timestamp = int(datetime.now().timestamp())
        try:
            voltage1 = float(DPS.query("MEAS:VOLT:DC? (@1)").strip())
            current1 = float(DPS.query("MEAS:CURR:DC? (@1)").strip())
            voltage2 = float(DPS.query("MEAS:VOLT:DC? (@2)").strip())
            current2 = float(DPS.query("MEAS:CURR:DC? (@2)").strip())
            if(paired == "OFF\n"):
                voltage3 = float(DPS.query("MEAS:VOLT:DC? (@3)").strip())
                current3 = float(DPS.query("MEAS:CURR:DC? (@3)").strip())
        except VisaIOError as e:
            QMessageBox.warning(self, "Warning", "Measurement Failed", QMessageBox.Ok)
    
        # Format data for InfluxDB
        voltage_data1 = f"E36312A,Channel=1 voltage={voltage1} {timestamp}"
        current_data1 = f"E36312A,Channel=1 current={current1} {timestamp}"
        voltage_data2 = f"E36312A,Channel=2 voltage={voltage2} {timestamp}"
        current_data2 = f"E36312A,Channel=2 current={current2} {timestamp}"
        if(paired == "OFF\n"):
            voltage_data3 = f"E36312A,Channel=3 voltage={voltage3} {timestamp}"
            current_data3 = f"E36312A,Channel=3 current={current3} {timestamp}"
        
        # Write data to InfluxDB
        if (int(DPS.query("OUTP:STAT? (@1)")) == 1):
            IC.write_data(voltage_data1, write_option=SYNCHRONOUS)
            IC.write_data(current_data1, write_option=SYNCHRONOUS)
        if (int(DPS.query("OUTP:STAT? (@2)")) == 1):
            IC.write_data(voltage_data2, write_option=SYNCHRONOUS)
            IC.write_data(current_data2, write_option=SYNCHRONOUS)
        if(paired == "OFF\n"):
            if (int(DPS.query("OUTP:STAT? (@3)")) == 1):
                IC.write_data(voltage_data3, write_option=SYNCHRONOUS)
                IC.write_data(current_data3, write_option=SYNCHRONOUS)

    def addRecording(self, bucketLabel, recordingLabel):
        self.layoutR = QVBoxLayout()
        self.startRecordingButton = QPushButton("Start Recording", clicked=lambda: self.startRecording(recordingLabel))
        self.layoutR.addWidget(self.startRecordingButton)
        
        self.stopRecordingButton = QPushButton("Stop Recording", clicked=lambda: self.stopRecording(recordingLabel))
        self.layoutR.addWidget(self.stopRecordingButton)

        self.frequencyLabel = QLabel("Set Frequency of Measurements")
        self.layoutR.addWidget(self.frequencyLabel)
        self.frequencyEntry = QLineEdit()
        self.frequencyEntry.setPlaceholderText("Enter time in seconds")
        self.layoutR.addWidget(self.frequencyEntry)
        self.frequencyButton = QPushButton("Set Frequency", clicked=lambda: self.setRecordingDelay(self.frequencyEntry.text(), self.currentFrequencyLabel, self.frequencyEntry))
        self.layoutR.addWidget(self.frequencyButton)

        self.newBucketLabel = QLabel("Create New Bucket")
        self.layoutR.addWidget(self.newBucketLabel)
        self.newBucketEntry = QLineEdit()
        self.newBucketEntry.setPlaceholderText("Enter bucket name")
        self.layoutR.addWidget(self.newBucketEntry)
        self.newBucketButton = QPushButton("Create Bucket", clicked=lambda: self.createBucket(self.newBucketEntry))
        self.layoutR.addWidget(self.newBucketButton)

        self.bucketSelectButton = QPushButton("Select Bucket", clicked=lambda: self.selectBucket(bucketLabel))
        self.layoutR.addWidget(self.bucketSelectButton)

        self.bucketsLabel = QLabel("Available Buckets")
        self.layoutR.addWidget(self.bucketsLabel)

        recording_layout.addLayout(self.layoutR)

        self.displayBuckets()

        self.layoutR.addWidget(buckets)

        recording_layout.addLayout(self.layoutR)
    
    def displayBuckets(self):
        global buckets
        global bucketList
        bucketList = buckets_api.find_buckets().buckets
        buckets.clear()
        bucketNames.clear()
        for bucket in bucketList:
            buckets.addItem(bucket.name)
            bucketNames.append(bucket.name)

    def selectBucket(self, bucketLabel): #when new bucket is created, the available indicies remain the same and any new indicies is refered back to 0
        global selectedBucket
        selectedIndices = buckets.selectedIndexes()
        if selectedIndices:
            ind = selectedIndices[0].row()
            selectedBucket = bucketNames[ind]
            bucketLabel.setText(f"Selected Bucket: {selectedBucket}")

    def createBucket(self, bucketNameEntry):
        bucketName = bucketNameEntry.text()
        bucketNameEntry.clear()
        
        if (bucketName not in bucketNames):
            retention_rules = BucketRetentionRules(type="expire", every_seconds=0)
            buckets_api.create_bucket(bucket_name=bucketName,
                                               retention_rules=retention_rules,
                                               org=org)
            self.displayBuckets()
        else:
            QMessageBox.warning(self, "Warning", "Bucket Already Exists", QMessageBox.Ok)

    def syncPowerSupply(self, DPS, button, ch, voltageLabel, currentLimitLabel):
        if (ch == 3 and paired != "OFF\n"):
            return
        if (int(DPS.query(f"OUTP:STAT? (@{ch})")) == 1):
            button.setText('ON')
            button.setStyleSheet("background-color: green")
        else:
            button.setText('OFF')
            button.setStyleSheet("background-color: red")

        voltage = float(DPS.query(f"VOLT? (@{ch})"))
        current = float(DPS.query(f"CURR? (@{ch})"))
        voltageLabel.setText(f'Voltage: {voltage} V')
        currentLimitLabel.setText(f'Current: {current} A')
    
    def syncOutputChannel(self, DPS, widget, update_timer):
        global paired
        global channels
        self.status = DPS.query("OUTP:PAIR?")
        if self.status != paired:
            paired = self.status
            if (paired == "OFF\n"):
                channels = [1, 2, 3]
            else:
                channels = [1, 2]
            update_timer.stop()
            update_timer.timeout.disconnect()
            del update_timer
            channel_layout.removeWidget(widget)
            widget.hide()
            widget.deleteLater()
            self.createChannel(3)

    def syncOutputChannel2(self, DPS, widget):
        global paired
        global channels
        self.status = DPS.query("OUTP:PAIR?")
        if self.status != paired:
            paired = self.status
            if (paired == "OFF\n"):
                channels = [1, 2, 3]
            else:
                channels = [1, 2]
            channel_layout.removeWidget(widget)
            widget.hide()
            widget.deleteLater()
            self.createChannel(3)

    def addChannel3Status(self):
        self.Ch3Label = QLabel("Set Channel 3 Status")
        control_layout.addWidget(self.Ch3Label)

        self.Ch3Layout = QHBoxLayout()
        self.indButton = QPushButton("Independent", clicked=lambda: x.changeOperationMode(self.DPS, "OFF"))
        self.seriesButton = QPushButton("Series", clicked=lambda: x.changeOperationMode(self.DPS, "SER"))
        self.parallelButton = QPushButton("Parallel", clicked=lambda: x.changeOperationMode(self.DPS, "PAR"))

        self.Ch3Layout.addWidget(self.indButton)
        self.Ch3Layout.addWidget(self.seriesButton)
        self.Ch3Layout.addWidget(self.parallelButton)

        control_layout.addLayout(self.Ch3Layout)