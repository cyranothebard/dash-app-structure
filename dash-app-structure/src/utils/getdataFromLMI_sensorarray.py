
import os
import threading
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

from utils.GoSdk_MsgHandler import MsgManager
from utils.loadConfig import load_config
cwd = os.getcwd()
config_file_path = os.path.join(cwd, 'dash-app-structure', 'config.json')
config = load_config(config_file_path)

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

class GoStampData(Structure):
    _fields_ = [("frameIndex", c_uint64), ("timestamp",c_uint64), ("encoder", c_int64), ("encoderAtZ", c_int64), ("status", c_uint64), ("id", c_uint32)]

class GoMeasurementData(Structure):
    _fields_ = [("numericVal", c_double), ("decision", c_uint8), ("decisionCode", c_uint8)]
    dataset = GoDataSet(kNULL)  # Define dataset as a class-level variable

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

def getVersionStr():
    version = ctypes.create_string_buffer(32)
    myVersion = GoSdk.GoSdk_Version()
    kApi.kVersion_Format(myVersion, version, 32)
    return str(ctypes.string_at(version))

def kObject_Destroy(object):
    if object != kNULL:
        kApi.xkObject_DestroyImpl(object, kFALSE)

def export_csv(data, config):
    """
    Export DataFrame to a CSV file.

    Args:
        data (pd.DataFrame): DataFrame to be exported.
        config (dict): Configuration containing the 'data_directory_CSV' setting.

    Returns:
        str: Filename of the exported CSV file.
    """
    data_directory_CSV = config.get('data_directory_CSV')
    # Check if the directory exists for CSV data and create if not
    if not os.path.exists(data_directory_CSV):
        os.makedirs(data_directory_CSV)

    unique_filename = os.path.join(data_directory_CSV, str(uuid.uuid4()) + ".csv")
    
    try:
        # Attempt to acquire an exclusive lock on the file
        file = open(unique_filename, 'w')
        data.to_csv(file, index=False)
        file.close()
        return unique_filename
    except IOError as e:
        # Failed to acquire lock, file is being accessed by another process
        logging.warning(f"Failed to export CSV. File '{unique_filename}' is being accessed by another process.")
    except Exception as e:
        logging.error(f"Error exporting CSV: {str(e)}")
    
    return None

def idToFeatureName(featureId):
    featurename = {
       125: 'Tongue Upper Radius',
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
    }
    return featurename.get(featureId, 'Unknown')

def receive_data(dataset):
    if not dataset:
        log_error("Invalid dataset. Exiting function.")
        return None
    
    sensor_data = None
    measurement_data_list = []
    
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

                measurement_data = {
                    'sensorID': sensor_data['sensorID'],  # Relationship with sensor data
                    'frameIndex': sensor_data['frameIndex'],  # Relationship with sensor data
                    'timeStamp': sensor_data['timeStamp'],  # Relationship with sensor data
                    'measurementID': measurementID,
                    'Value': measurementData.numericVal,
                    'Decision': str(measurementData.decision),
                    'FeatureName': idToFeatureName(measurementID)
                }
                
                measurement_data_list.append(measurement_data)

    # Convert lists to DataFrame
    measurement_data_batch = pd.DataFrame(measurement_data_list)
    
    if measurement_data_batch.empty:
        log_error("No valid measurement data found.")
        return None
    
    # Drop any empty or all-NA columns
    measurement_data_batch = measurement_data_batch.dropna(axis=1, how='all')

    # Export data in a separate thread
    thread = threading.Thread(target=export_csv, args=(measurement_data_batch, config))
    thread.daemon = True  # Set the thread as a daemon to stop when the main thread stops
    thread.start()

    # Export data
    #csv_filename = export_csv(measurement_data_batch)
    
    #log_info("Measurement data exported to CSV file: {}".format(csv_filename))

    # Destroy the dataset object
    kObject_Destroy(dataset)

    return measurement_data_batch


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

def run_measurement_data_collection():
    # Instantiate system objects
    api = kAssembly(kNULL)
    system = GoSystem(kNULL)
    sensor = GoSensor(kNULL)
    dataset = GoDataSet(kNULL)
    dataObj = GoDataMsg(kNULL)
    changed = kBool(kNULL)

    logging.info('Sdk Version is: ' + getVersionStr())

    GoSdk.GoSdk_Construct(byref(api))  # Build API
    GoSdk.GoSystem_Construct(byref(system), kNULL)  # Construct sensor system

    # Connect to the sensor
    sensor_IP = b'127.0.0.1'  # default for local emulator is 127.0.0.1
    array_sensor_IP = b'192.168.92.111'
    overhead_sensor_IP = b'192.168.92.107'
    ipAddr_ref = kIpAddress()
    kApi.kIpAddress_Parse(byref(ipAddr_ref), array_sensor_IP)
    GoSdk.GoSystem_FindSensorByIpAddress(system, byref(ipAddr_ref), byref(sensor))
    
    # Connect to sensor via ID
    array_sensor_ID = 172054
    overhead_sensor_ID = 181521
    GoSdk.GoSystem_FindSensorById(system, array_sensor_ID, byref(sensor))
    

    #GoSdk.GoSensor_Start(sensor)  # Start the sensor to gather data
    #GoSdk.GoSensor_Connect(sensor)
    GoSdk.GoSystem_EnableData(system, kTRUE)  # Enable the sensor's data channel to receive measurement data
    logging.info(" Sensor Connected!")

    # Initialize message handler manager
    Mgr = MsgManager(GoSdk, system, dataset)

    # Set data handler which spawns a worker thread to receive input data
    Mgr.SetDataHandler(RECEIVE_TIMEOUT, receive_data)

    # Issue a stop then start in case the emulator is still running. For live sensors, only a start is needed.
    #GoSdk.GoSensor_Stop(sensor) 
    #GoSdk.GoSensor_Start(sensor)
    
    # Do nothing
    while input() != "exit":
        pass
    
    # Can close thread manually by recalling data handler with kNull passed
    # Mgr.SetDataHandler(GoSdk, system, dataset, RECEIVE_TIMEOUT, kNULL)

    # Destroy the system object and api
    kObject_Destroy(system)
    kObject_Destroy(api)

if __name__ == "__main__":
# Instantiate system objects
    api = kAssembly(kNULL)
    system = GoSystem(kNULL)
    sensor = GoSensor(kNULL)
    dataset = GoDataSet(kNULL)
    dataObj = GoDataMsg(kNULL)
    changed = kBool(kNULL)

    print('Sdk Version is: ' + getVersionStr())

    GoSdk.GoSdk_Construct(byref(api))  # Build API
    GoSdk.GoSystem_Construct(byref(system), kNULL)  # Construct sensor system

    #connect to sensor via IP
    sensor_IP = b'127.0.0.1' #default for local emulator is 127.0.0.1 
    array_sensor_IP = b'192.168.92.111'
    overhead_sensor_IP = b'192.168.92.107'
    ipAddr_ref = kIpAddress()
    kApi.kIpAddress_Parse(byref(ipAddr_ref), sensor_IP)
    GoSdk.GoSystem_FindSensorByIpAddress(system,byref(ipAddr_ref),byref(sensor))
    
    #connect to sensor via ID
    array_sensor_ID = 172054
    overhead_sensor_ID = 181521
    GoSdk.GoSystem_FindSensorById(system, array_sensor_ID, byref(sensor))

    GoSdk.GoSensor_Connect(sensor)  # Connect to the sensor
    GoSdk.GoSystem_EnableData(system, kTRUE)  # Enable the sensor's data channel to receive measurement data
    #GoSdk.GoSensor_Start(sensor)  # Start the sensor to gather data
    print("connected!")

    #Initialize message handler manager
    Mgr = MsgManager(GoSdk, system, dataset)

    #Set data handler which spawns a worker thread to recieve input data
    Mgr.SetDataHandler(RECEIVE_TIMEOUT, receive_data)

    #Issue a stop then start incase the emulator is still running. For live sensors, only a start is needed.
    GoSdk.GoSensor_Stop(sensor) 
    GoSdk.GoSensor_Start(sensor)
    
    #Do nothing
    while(input() != "exit"):
        pass
    
    #Can close thread manually by recalling data handler with kNull passed
    #Mgr.SetDataHandler(GoSdk, system, dataset, RECEIVE_TIMEOUT, kNULL)

    ### Destroy the system object and api
    kObject_Destroy(system)
    kObject_Destroy(api)
