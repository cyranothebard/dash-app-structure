
import datetime
import os
import threading
import time
import pandas as pd
import msvcrt
import uuid
import ctypes
import logging
import csv
import cv2
import numpy as np
import boto3
from ctypes import Structure, POINTER, byref, c_byte, c_char, c_int16, c_short, c_uint32, c_uint64, c_uint8, c_int32, c_int64, c_void_p, c_bool, c_double, c_ulonglong
from array import array
from PIL import Image, ImageDraw
import random
import string
from pyModbusTCP.client import ModbusClient

from utils.GoSdk_MsgHandler import MsgManager
from utils.loadConfig import load_config

cwd = os.getcwd()
config_file_path = os.path.join(cwd, 'dash-app-structure', 'config.json')
config = load_config(config_file_path)

ALLOW_R_L = ['127.0.0.1', '192.168.92.104']
ALLOW_W_L = ['127.0.0.1']

### Load Api
#gosdkInstallPath = config.get('gosdkInstallPath')
#path_to_GoSdkdll = gosdkInstallPath+r'\GO_SDK\bin\win64\GoSdk.dll'
#path_to_kApidll = gosdkInstallPath+r'\GO_SDK\bin\win64\kApi.dll'
path_to_kApidll = config.get('path_to_kApidll')
kApi = ctypes.windll.LoadLibrary(path_to_kApidll)
path_to_GoSdkdll = config.get('path_to_GoSdkdll')
GoSdk = ctypes.windll.LoadLibrary(path_to_GoSdkdll)

### Constant Declaration and Instantiation
kNULL = 0
kTRUE = 1
kFALSE = 0
kOK = 1
GO_DATA_MESSAGE_TYPE_MEASUREMENT = 10
GO_DATA_MESSAGE_TYPE_SURFACE_INTENSITY = 9
GO_DATA_MESSAGE_TYPE_UNIFORM_SURFACE = 8
GO_DATA_MESSAGE_TYPE_UNIFORM_PROFILE = 7
GO_DATA_MESSAGE_TYPE_STAMP = 0
RECEIVE_TIMEOUT = 10000

### Gocator DataType Declarations
kObject = ctypes.c_void_p
kValue = ctypes.c_uint32
kSize = ctypes.c_ulonglong
kAssembly = ctypes.c_void_p
GoSystem = ctypes.c_void_p
GoSensor = ctypes.c_void_p
GoDataSet = ctypes.c_void_p
GoDataMsg = ctypes.c_void_p
kChar = ctypes.c_byte
kBool = ctypes.c_bool
kCall = ctypes.c_bool
kCount = ctypes.c_uint32

measurement_data_list = []

class GoStampData(Structure):
    _fields_ = [("frameIndex", c_uint64), ("timestamp",c_uint64), ("encoder", c_int64), ("encoderAtZ", c_int64), ("status", c_uint64), ("id", c_uint32)]

class GoMeasurementData(Structure):
    _fields_ = [("numericVal", c_double), ("decision", c_uint8), ("decisionCode", c_uint8)]
    dataset = GoDataSet(kNULL)  # Define dataset as a class-level variable

class getDataFromLMICameras:
    """ Declaring static variables for working directory, config files and GOSDK variables"""
    def __init__(self) -> None:
        self.measurement_data_list = []
        self.cwd = os.getcwd()
        self.config_file_path = os.path.join(cwd, 'dash-app-structure', 'config.json')
        self.config = load_config(config_file_path)
        self.door_ID = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        self.modbusClient= ModbusClient(host="192.168.92.104", port=502, auto_open=True)
        
    def receive_surface_data(self, dataset):
        if not dataset:
            self.log_error("Invalid dataset. Exiting function.")
            return None
        
        sensor_data = None
        
        for i in range(GoSdk.GoDataSet_Count(dataset)):
            k_object_address = GoSdk.GoDataSet_At(dataset, i)
            dataObj = GoDataMsg(k_object_address)
            
            if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_STAMP:
                stampMsg = dataObj
                msgCount = GoSdk.GoStampMsg_Count(stampMsg)
                
                for k in range(msgCount):
                    stampDataPtr = GoSdk.GoStampMsg_At(stampMsg, k)
                    stampData = stampDataPtr.contents

                    sensor_data = {
                        'sensorID': stampData.id,
                        'frameIndex': stampData.frameIndex,
                        'timeStamp': stampData.timestamp
                    }
            
            if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_MEASUREMENT:
                measurementMsg = dataObj
                msgCount = GoSdk.GoMeasurementMsg_Count(measurementMsg)

                for k in range(msgCount):
                    measurementDataPtr = GoSdk.GoMeasurementMsg_At(measurementMsg, k)
                    measurementData = measurementDataPtr.contents
                    measurementID = GoSdk.GoMeasurementMsg_Id(measurementMsg)

                    if measurementData.numericVal != -1.7976931348623157e+308:
                        measurement_data = {
                            'doorID': self.door_ID,
                            'sensorID': sensor_data['sensorID'],  # Relationship with sensor data
                            'frameIndex': sensor_data['frameIndex'],  # Relationship with sensor data
                            'timeStamp': sensor_data['timeStamp'],  # Relationship with sensor data
                            'measurementID': measurementID,
                            'Value': measurementData.numericVal,
                            'Decision': measurementData.decision,
                            'FeatureName': self.idToFeatureName(measurementID)
                        }
                        self.measurement_data_list.append(measurement_data)
                    #log error
                    if measurementData.numericVal == -1.7976931348623157e+308:
                        self.log_error("value is invalid")

            if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_UNIFORM_SURFACE:
                pass

        # Convert lists to DataFrame
        measurement_data_batch = pd.DataFrame(self.measurement_data_list)
        measurement_data_batch['timeStamp'] = pd.Timestamp.now()
        grouped_data = measurement_data_batch.groupby(['timeStamp','doorID', 'measurementID', 'FeatureName']).agg(
                                                                  percent_pass=('Decision', 'mean'),
                                                                  average_value=('Value', 'mean'),
                                                                  min_value=('Value', 'min'),
                                                                  max_value=('Value', 'max'),
                                                                  value_count=('Value', 'count'),
                                                                  standard_deviation=('Value', 'std'),
                                                                  variance=('Value', 'var'))
        self.trigger_stacklight(grouped_data)
        # Reset the global variable list
        self.measurement_data_list = []
        
        if measurement_data_batch.empty or grouped_data.empty:
            self.log_error("No valid measurement data found.")
            return None
        
        # Drop any empty or all-NA columns
        measurement_data_batch = measurement_data_batch.dropna(axis=1, how='all')
        grouped_data = grouped_data.dropna(axis=1, how='all')

        
        profile_data_directory_CSV = self.config.get('data_directory_CSV')
        grouped_data_directory_CSV = self.config.get('grouped_data_directory_CSV')

        #Export data in a separate thread
        #thread = threading.Thread(target=export_csv, args=(measurement_data_batch, config))
        #thread.daemon = True  # Set the thread as a daemon to stop when the main thread stops
        #thread.start()
        self.export_csv(measurement_data_batch, profile_data_directory_CSV, is_index=False)
        self.export_csv(grouped_data, grouped_data_directory_CSV, is_index=True)

        # Assigning a new door ID
        self.door_ID = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                
        #log_info("Measurement data exported to CSV file: {}".format(csv_filename))

        # Destroy the dataset object
        self.kObject_Destroy(dataset)

        return True
        
    def receive_data(self, dataset):
        if not dataset:
            self.log_error("Invalid dataset. Exiting function.")
            return None
        
        sensor_data = None
        
        for i in range(GoSdk.GoDataSet_Count(dataset)):
            k_object_address = GoSdk.GoDataSet_At(dataset, i)
            dataObj = GoDataMsg(k_object_address)
            
            if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_STAMP:
                stampMsg = dataObj
                msgCount = GoSdk.GoStampMsg_Count(stampMsg)
                
                for k in range(msgCount):
                    stampDataPtr = GoSdk.GoStampMsg_At(stampMsg, k)
                    stampData = stampDataPtr.contents

                    sensor_data = {
                        'sensorID': stampData.id,
                        'frameIndex': stampData.frameIndex,
                        'timeStamp': stampData.timestamp
                    }

            if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_MEASUREMENT:
                measurementMsg = dataObj
                msgCount = GoSdk.GoMeasurementMsg_Count(measurementMsg)

                for k in range(msgCount):
                    measurementDataPtr = GoSdk.GoMeasurementMsg_At(measurementMsg, k)
                    measurementData = measurementDataPtr.contents
                    measurementID = GoSdk.GoMeasurementMsg_Id(measurementMsg)

                    if measurementData.numericVal != -1.7976931348623157e+308:
                        measurement_data = {
                            'doorID': self.door_ID,
                            'sensorID': sensor_data['sensorID'],  # Relationship with sensor data
                            'frameIndex': sensor_data['frameIndex'],  # Relationship with sensor data
                            'timeStamp': sensor_data['timeStamp'],  # Relationship with sensor data
                            'measurementID': measurementID,
                            'Value': measurementData.numericVal,
                            'Decision': measurementData.decision,
                            'FeatureName': self.idToFeatureName(measurementID)
                        }
                        self.measurement_data_list.append(measurement_data)
                    #log error
                    if measurementData.numericVal == -1.7976931348623157e+308:
                        self.log_error("value is invalid")
        
        #log_info("Measurement data exported to CSV file: {}".format(csv_filename))

        # Destroy the dataset object
        self.kObject_Destroy(dataset)

        # return measurement_data_batch
        return True

    def log_info(self, message):
        logging.info(message)

    def log_error(self, message):
        logging.error(message)

    def getVersionStr(self):
        version = ctypes.create_string_buffer(32)
        myVersion = GoSdk.GoSdk_Version()
        kApi.kVersion_Format(myVersion, version, 32)
        return str(ctypes.string_at(version))

    def kObject_Destroy(self, object):
        if object != kNULL:
            kApi.xkObject_DestroyImpl(object, kFALSE)

    def export_csv(self, data, data_directory_CSV, is_index):
        """
        Export DataFrame to a CSV file.

        Args:
            data (pd.DataFrame): DataFrame to be exported.
            config (dict): Configuration containing the 'data_directory_CSV' setting.

        Returns:
            str: Filename of the exported CSV file.
        """
        # Check if the directory exists for CSV data and create if not
        if not os.path.exists(data_directory_CSV):
            os.makedirs(data_directory_CSV)
        # Get the current Unix timestamp
        timestamp = time.time()

        # Convert the Unix timestamp to a datetime object
        datetime_obj = str(timestamp)
        # unique_filename = os.path.join(data_directory_CSV, str(uuid.uuid4()) + datetime_obj + ".csv")
        unique_filename = os.path.join(data_directory_CSV, str(self.door_ID) + '_' + datetime_obj + '.csv')

        try:
            # Attempt to acquire an exclusive lock on the file
            file = open(unique_filename, 'w')
            data.to_csv(file, index=is_index)
            file.close()
            return unique_filename
        except IOError as e:
            # Failed to acquire lock, file is being accessed by another process
            logging.warning(f"Failed to export CSV. File '{unique_filename}' is being accessed by another process.")
        except Exception as e:
            logging.error(f"Error exporting CSV: {str(e)}")
        
        return None

    def idToFeatureName(self, featureId):
        featurename = {
        125: 'Tongue Upper Radius',
        123: 'Tongue Middle Radius',
        121: 'Tongue Lower Radius',
        116: 'Tongue Hem Height',
        96: 'Groove Seat Distance, Outer',
        90: 'Groove Seat Distance, Inner',
        109: 'Groove Side Hem Height',
        80: 'Groove Width, Inner',
        77: 'Groove Width, Outer',
        68: 'Groove Height',
        66: 'Groove upper Claw Height',
        63: 'Groove Upper Bump Height',
        24: 'Clip length/Distance',
        23: 'Clip length/Width',
        106: 'Groove Radius, Upper Outer',
        103: 'Groove Radius, Middle',
        100: 'Groove Radius, Lower Inner',
        18: 'Groove Radius, Lower Outer',
        50: 'Tongue Width, Upper',
        43: 'Tongue Width',
        38: 'Tongue Lower Leg Height',
        32: 'Tongue Middle Leg Height',
        14: 'Tongue Leg Height',
        15: 'Door Length',
        26: 'Oil Canning - top',
        27: 'Oil Canning - middle',
        29: 'Oil Canning - bottom'
        }
        return featurename.get(featureId, 'Unknown')
    
    def run_measurement_data_collection(self):
        # Instantiate system objects
        api = kAssembly(kNULL)
        system = GoSystem(kNULL)
        sensor = GoSensor(kNULL)
        dataset = GoDataSet(kNULL)
        dataObj = GoDataMsg(kNULL)
        changed = kBool(kNULL)

        logging.info('Sdk Version is: ' + self.getVersionStr())

        GoSdk.GoSdk_Construct(byref(api))  # Build API
        GoSdk.GoSystem_Construct(byref(system), kNULL)  # Construct sensor system

        #connect to sensor via IP
        # sensor_IP = b'127.0.0.1' #default for local emulator is 127.0.0.1 
        # array_sensor_IP = b'192.168.92.101'
        # overhead_sensor_IP = b'192.168.92.107'
        # ipAddr_ref = kIpAddress()
        # kApi.kIpAddress_Parse(byref(ipAddr_ref), array_sensor_IP)
        # GoSdk.GoSystem_FindSensorByIpAddress(system,byref(ipAddr_ref),byref(sensor))
        
        # connect to sensor via ID
        array_sensor_ID = 172054
        overhead_sensor_ID = 181521
        GoSdk.GoSystem_FindSensorById(system, array_sensor_ID, byref(sensor))

        GoSdk.GoSensor_Connect(sensor)  # Connect to the sensor
        GoSdk.GoSystem_EnableData(system, kTRUE)  # Enable the sensor's data channel to receive measurement data
        #GoSdk.GoSensor_Start(sensor)  # Start the sensor to gather data
        print("Array Cameras Connected!")

        #Initialize message handler manager
        Mgr = MsgManager(GoSdk, system, dataset)

        #Set data handler which spawns a worker thread to recieve input data
        Mgr.SetDataHandler(RECEIVE_TIMEOUT, self.receive_data)

        #Issue a stop then start incase the emulator is still running. For live sensors, only a start is needed.
        #GoSdk.GoSensor_Stop(sensor) 
        GoSdk.GoSensor_Start(sensor)
        
        #Do nothing
        while(input() != "exit"):
            pass
        
        #Can close thread manually by recalling data handler with kNull passed
        #Mgr.SetDataHandler(GoSdk, system, dataset, RECEIVE_TIMEOUT, kNULL)

        ### Destroy the system object and api
        self.kObject_Destroy(system)
        self.kObject_Destroy(api)

    def run_surface_data_collection(self):
        # Instantiate system objects
        api = kAssembly(kNULL)
        system = GoSystem(kNULL)
        sensor = GoSensor(kNULL)
        dataset = GoDataSet(kNULL)
        dataObj = GoDataMsg(kNULL)
        changed = kBool(kNULL)

        logging.info('Sdk Version is: ' + self.getVersionStr())

        GoSdk.GoSdk_Construct(byref(api))  # Build API
        GoSdk.GoSystem_Construct(byref(system), kNULL)  # Construct sensor system

        #connect to sensor via IP
        # sensor_IP = b'127.0.0.1' #default for local emulator is 127.0.0.1 
        # # array_sensor_IP = b'192.168.92.111'
        # overhead_sensor_IP = b'192.168.92.107'
        # ipAddr_ref = kIpAddress()
        # kApi.kIpAddress_Parse(byref(ipAddr_ref), overhead_sensor_IP)
        # GoSdk.GoSystem_FindSensorByIpAddress(system,byref(ipAddr_ref),byref(sensor))
        
        # connect to sensor via ID
        array_sensor_ID = 172054
        overhead_sensor_ID = 181521
        GoSdk.GoSystem_FindSensorById(system, overhead_sensor_ID, byref(sensor))

        GoSdk.GoSensor_Connect(sensor)  # Connect to the sensor
        GoSdk.GoSystem_EnableData(system, kTRUE)  # Enable the sensor's data channel to receive measurement data
        #GoSdk.GoSensor_Start(sensor)  # Start the sensor to gather data
        print("Surface Camera Connected!")

        #Initialize message handler manager
        Mgr = MsgManager(GoSdk, system, dataset)

        #Set data handler which spawns a worker thread to recieve input data
        Mgr.SetDataHandler(RECEIVE_TIMEOUT, self.receive_surface_data)

        #Issue a stop then start incase the emulator is still running. For live sensors, only a start is needed.
        #GoSdk.GoSensor_Stop(sensor) 
        GoSdk.GoSensor_Start(sensor)
        
        #Do nothing
        while(input() != "exit"):
            pass
        
        #Can close thread manually by recalling data handler with kNull passed
        #Mgr.SetDataHandler(GoSdk, system, dataset, RECEIVE_TIMEOUT, kNULL)

        ### Destroy the system object and api
        # self.kObject_Destroy(system)
        # self.kObject_Destroy(api)

    def trigger_stacklight(self, grouped_data):
    # Initialize the Modbus client (TCP always open)
        if (self.modbusClient.open()) != True:
            self.modbusClient= ModbusClient(host="192.168.92.104", port=502, auto_open=True)
        else: 
            pass
        
        # c.connect()
    # set empty counts
        count_green = 0
        count_amber = 0
        count_red = 0
    # set coil hex addresses
        coil_red = 0x01E8
        coil_amber = 0x01E9
        coil_green = 0x01EA
    
    # aggregate percent_pass data
        for i in range(len(grouped_data)):
            if grouped_data['percent_pass'][i] >= 0.75:
                count_green +=1
            elif grouped_data['percent_pass'][i] >= 0.50 and grouped_data['percent_pass'][i] < 0.75:
                count_amber +=1
            elif grouped_data['percent_pass'][i] < 0.50:
                count_red +=1
        # Read 16-bit registers at Modbus address 0
        if count_green > (count_amber + count_red):
            self.modbusClient.write_single_coil(coil_green, True)
            time.sleep(5)
            print('Inspection Passed')
            self.modbusClient.write_single_coil(coil_green, False)
        elif count_green <= (count_amber + count_red):
            self.modbusClient.write_single_coil(coil_amber,True)
            time.sleep(5)
            print('Inspection Marginal')
            self.modbusClient.write_single_coil(coil_amber, False)
        elif count_red > (count_amber + count_green):
            self.modbusClient.write_single_coil(coil_red, True)
            time.sleep(5)
            print('Inspection Failed')
            self.modbusClient.write_single_coil(coil_red, False)

class kIpAddress(Structure):
    _fields_ = [("kIpVersion", c_int32),("kByte",c_char*16)]

### Define Argtype and Restype
GoSdk.GoDataSet_At_argtypes = [kObject, kSize]
GoSdk.GoDataSet_At.restype = kObject
GoSdk.GoDataMsg_Type.argtypes = [kObject]
GoSdk.GoDataMsg_Type.restype = kValue
GoSdk.GoSurfaceMsg_RowAt.restype = c_int64
GoSdk.GoUniformSurfaceMsg_RowAt.restype = ctypes.POINTER(ctypes.c_int16)
GoSdk.GoSurfaceIntensityMsg_RowAt.restype = ctypes.POINTER(ctypes.c_uint8)
GoSdk.GoStampMsg_At.restype = ctypes.POINTER(GoStampData)
GoSdk.GoMeasurementMsg_At.restype = ctypes.POINTER(GoMeasurementData)
GoSdk.GoResampledProfileMsg_At.restype = ctypes.POINTER(ctypes.c_short)
