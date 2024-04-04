#Refactor this so main can be called from dash layout.py to run main function and continue to connect and read data from Lmi device
import os
import pandas as pd
import uuid
import ctypes
import csv
import cv2
import time
import numpy as np
import boto3
from ctypes import Structure, POINTER, byref, c_byte, c_char, c_int16, c_short, c_uint32, c_uint64, c_uint8, c_int32, c_int64, c_void_p, c_bool, c_double, c_ulonglong
from array import array
from PIL import Image, ImageDraw

from utils.GoSdk_MsgHandler import MsgManager

### Load Api
gosdkInstallPath = os.environ.get('GO_SDK_4')
path_to_kApidll = gosdkInstallPath+r"\GO_SDK\bin\win64\kApi.dll"
#path_to_kApidll = r'F:\GO_SDK\bin\win64\kApi.dll' 
kApi = ctypes.windll.LoadLibrary(path_to_kApidll)
path_to_GoSdkdll = r'F:\GO_SDK\bin\win64\GoSdk.dll'
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

#@staticmethod
def getVersionStr():
    version = ctypes.create_string_buffer(32)
    myVersion = GoSdk.GoSdk_Version()
    kApi.kVersion_Format(myVersion, version, 32)
    return str(ctypes.string_at(version))

#@staticmethod
def kObject_Destroy(object):
    if (object != kNULL):
        kApi.xkObject_DestroyImpl(object, kFALSE)

#@staticmethod
def export_csv(data):
    """
    Export DataFrame to a CSV file.

    Args:
        data (pd.DataFrame): DataFrame to be exported.

    Returns:
        str: Filename of the exported CSV file.
    """
    utils_folder = os.path.dirname(__file__)# Get the path of the utils folder
    src_folder = os.path.dirname(utils_folder) # Get the path of the src folder
    measurmentData_folder = os.path.join(src_folder, '..', 'data', 'measurmentDataCSV')
    unique_filename = os.path.join(measurmentData_folder, str(uuid.uuid4()) + ".csv")
    data.to_csv(unique_filename, index=False)
    return unique_filename

#@staticmethod
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

#@staticmethod
def receive_data(dataset):
    """
    Process received data from the sensor dataset.
    
    Args:
        dataset: Dataset received from the sensor.

    Returns:
        str: Message indicating successful data reception.
    """
    if not dataset:
        print("Invalid dataset. Exiting function.")
        return None

    measurement_data = pd.DataFrame(columns=['ID', 'Value', 'Decision', 'FeatureName', 'TimeStamp'])
    measurement_data_batch = pd.DataFrame(columns=['ID', 'Value', 'Decision', 'FeatureName', 'TimeStamp'])

    for i in range(GoSdk.GoDataSet_Count(dataset)):
        k_object_address = GoSdk.GoDataSet_At(dataset, i)
        dataObj = GoDataMsg(k_object_address)

        if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_MEASUREMENT:
            measurementMsg = dataObj
            msgCount = GoSdk.GoMeasurementMsg_Count(measurementMsg)

            for k in range(msgCount):
                measurementDataPtr = GoSdk.GoMeasurementMsg_At(measurementMsg, k)
                measurementData = measurementDataPtr.contents
                measurementID = GoSdk.GoMeasurementMsg_Id(measurementMsg)

                measurement_data_dict = [{
                    'ID': measurementID,
                    'Value': measurementData.numericVal,
                    'Decision': measurementData.decision,
                    'FeatureName': (idToFeatureName(measurementID)),
                    'TimeStamp': pd.to_datetime('now')
                }]

                measurement_data = pd.concat([measurement_data, pd.DataFrame(measurement_data_dict)], ignore_index=True)
                # print('measurement_data_batch:')
                measurement_data_batch = pd.concat([measurement_data_batch, pd.DataFrame(measurement_data)], ignore_index=True)
    if measurement_data.empty:
        print("No valid measurement data found.")
        return None
    
    export_csv(measurement_data_batch)
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

    print('Sdk Version is: ' + getVersionStr())

    GoSdk.GoSdk_Construct(byref(api))  # Build API
    GoSdk.GoSystem_Construct(byref(system), kNULL)  # Construct sensor system

    # Connect to the sensor
    sensor_IP = b'127.0.0.1'  # default for local emulator is 127.0.0.1
    array_sensor_IP = b'192.168.92.111'
    overhead_sensor_IP = b'192.168.92.107'
    ipAddr_ref = kIpAddress()
    kApi.kIpAddress_Parse(byref(ipAddr_ref), sensor_IP)
    GoSdk.GoSystem_FindSensorByIpAddress(system, byref(ipAddr_ref), byref(sensor))
    
    # Connect to sensor via ID
    array_sensor_ID = 172054
    overhead_sensor_ID = 181521
    GoSdk.GoSystem_FindSensorById(system, array_sensor_ID, byref(sensor))

    GoSdk.GoSensor_Connect(sensor)
    GoSdk.GoSystem_EnableData(system, kTRUE)  # Enable the sensor's data channel to receive measurement data
    # GoSdk.GoSensor_Start(sensor)  # Start the sensor to gather data
    print("Connected!")

    # Initialize message handler manager
    Mgr = MsgManager(GoSdk, system, dataset)

    # Set data handler which spawns a worker thread to receive input data
    Mgr.SetDataHandler(RECEIVE_TIMEOUT, receive_data)

    # Issue a stop then start in case the emulator is still running. For live sensors, only a start is needed.
    GoSdk.GoSensor_Stop(sensor) 
    GoSdk.GoSensor_Start(sensor)
    
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
