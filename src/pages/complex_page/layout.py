# notes
'''
This directory is meant to be for a specific page.
We will define the page and import any page specific components that we define in this directory.
This file should serve the layouts and callbacks.
The callbacks could be in their own file, but you'll need to make sure to import the file so they load.
'''

# package imports
import dash
from dash import html, Dash, dash_table
import dash_bootstrap_components as dbc
from flask import Flask
import pandas as pd
import numpy as np 
import os 
import scipy

# local imports
# from .comp1 import random_component
from components import create_profile_image_card
from utils import GoSdk_MsgHandler
from utils.data_sensorarray import ReceiveData, groupby_and_export, map_id_to_name

# ##LMI internal Python script

from asyncio.windows_events import NULL
import os
import ctypes
from ctypes import *
from array import *
import csv
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
import GoSdk_MsgHandler
import uuid
import cv2
import time
import boto3


### Load Api
# Please define your System Environment Variable as GO_SDK_4. It should reference the root directory of the SDK package.
SdkPath = os.environ['GO_SDK_4']
#Windows
kApi = ctypes.windll.LoadLibrary(os.path.join(SdkPath, 'bin', 'win64', 'kApi.dll'))
GoSdk = ctypes.windll.LoadLibrary(os.path.join(SdkPath, 'bin', 'win64', 'GoSdk.dll'))

#Linux
#kApi = ctypes.cdll.LoadLibrary(os.path.join(SdkPath, 'lib', 'linux_x64d', 'libkApi.dll'))
#GoSdk = ctypes.cdll.LoadLibrary(os.path.join(SdkPath, 'lib', 'linux_x64d', 'libGoSdk.dll'))

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

def getVersionStr():
    version = ctypes.create_string_buffer(32)
    myVersion = GoSdk.GoSdk_Version()
    kApi.kVersion_Format(myVersion, version, 32)
    return str(ctypes.string_at(version))

def kObject_Destroy(object):
    if (object != kNULL):
        kApi.xkObject_DestroyImpl(object, kFALSE)

### generate dummy data for experimentation
df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/c78bf172206ce24f77d6363a2d754b59/raw/c353e8ef842413cae56ae3920b8fd78468aa4cb2/usa-agricultural-exports-2011.csv')
cwd = os.getcwd()
order_data_path = os.path.join(cwd, 'dash-app-structure', 'src', 'assets', 'data', 'RPS Example Data 1.csv')
order_data = pd.read_csv(order_data_path)
order_data = order_data[order_data['workorder']==25512169]
df_orderdata = dash_table.DataTable(
        data=order_data.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in order_data.columns])
df_sensor_sample = pd.DataFrame({
    'tongue_hem_height': scipy.stats.truncnorm.rvs(a=0.1, b=0.3, loc=0.2, scale=0.05, size=3),
    'groove_hem_height': scipy.stats.truncnorm.rvs(a=0.1, b=0.3, loc=0.2, scale=0.05, size=3),
    'face_dovetail_height': scipy.stats.truncnorm.rvs(a=0.3, b=0.4, loc=0.345, scale=0.05, size=3),
    'back_dovetail_height': scipy.stats.truncnorm.rvs(a=0.1, b=0.4, loc=0.285, scale=0.05, size=3),
    'pan_width': scipy.stats.truncnorm.rvs(a=17.5, b=18.5, loc=18, scale=0.05, size=3),
    'tongue_leg_height': scipy.stats.truncnorm.rvs(a=1.65, b=2, loc=1.875, scale=0.05, size=3),
    'groove_leg_height': scipy.stats.truncnorm.rvs(a=1.65, b=2, loc=1.875, scale=0.05, size=3),
    'tongue_shadow_line': scipy.stats.truncnorm.rvs(a=0.035, b=0.07, loc=0.05, scale=0.05, size=3),
    'groove_shadow_line': scipy.stats.truncnorm.rvs(a=0.035, b=0.07, loc=0.05, scale=0.05, size=3),
})
df_sensor_sample = np.trunc(1000*df_sensor_sample) / 1000

# print(df_sensor_sample)
def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])
    # dataframe = ReceiveData()
    # return dash_table.DataTable(
    #     data=dataframe.to_dict('records'),
    #     columns=[{'name': col, 'id': col} for col in dataframe.columns],
    #     style_data_conditional = sensor_data_conditional
    # )
    
sensor_data_conditional = [
    {
        'if': {
            'filter_query': '{tongue_hem_height} < 0.18 or {tongue_hem_height} > 0.22',
            'column_id': 'tongue_hem_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{groove_hem_height} < 0.18 or {groove_hem_height} > 0.22',
            'column_id': 'groove_hem_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{face_dovetail_height} < 0.325 or {face_dovetail_height} > 0.365',
            'column_id': 'face_dovetail_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{back_dovetail_height} < 0.265 or {back_dovetail_height} > 0.305',
            'column_id': 'back_dovetail_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{tongue_leg_height} < 1.85 or {tongue_leg_height} > 1.90',
            'column_id': 'tongue_leg_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{groove_leg_height} < 1.85 or {groove_leg_height} > 1.90',
            'column_id': 'groove_leg_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{tongue_shadow_line} < 0.045 or {tongue_shadow_line} > 0.055',
            'column_id': 'tongue_shadow_line'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{groove_shadow_line} < 0.045 or {groove_shadow_line} > 0.055',
            'column_id': 'groove_shadow_line'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{pan_width} < 18.00 or {pan_width} > 18.045',
            'column_id': 'pan_width'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
   {
        'if': {
            'filter_query': '{pan_width} < 21.00 or {pan_width} > 21.045',
            'column_id': 'pan_width'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{pan_width} < 24.00 or {pan_width} > 24.045',
            'column_id': 'pan_width'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    #  {
    #     'if': {
    #         'filter_query': '{'Work Order'} == 10264754',
    #         'column_id': 'Work Order'
    #            },
    #     'backgroundColor': 'red',
    #     'color': 'white',
    # },
]

dash.register_page(
    __name__,
    path='/complex',
    title='Process Monitoring'
)
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    # use_pages=True,    # turn on Dash pages
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME
    ],  # fetch the proper css items we want
    meta_tags=[
        {   # check if device is a mobile device. This is a must if you do any mobile styling
            'name': 'viewport',
            'content': 'width=device-width, initial-scale=1'
        }
    ],
    suppress_callback_exceptions=True,
    title='Dash app structure'
)

layout = html.Div(
    [
        # html.H3('Random component'),
        # random_component,
        html.H3('Garage Door Profiles'),
        dbc.Row(
            [
                create_profile_image_card('70E100', 'left'), # DEBUGGING - function results in broken images
                create_profile_image_card('70E100', 'right')
            ]
        ),
        html.H3('Measurement Data'),
        # generate_table(ReceiveData),
        generate_table(df_sensor_sample),
        html.H3('Order Data'),
        df_orderdata #.loc[df_orderdata['workorder']==25512169]
        ], 
        # NumberFactAIO(number=1)
    )

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
    sensor_IP = b"127.0.0.1" #default for local emulator is 127.0.0.1 
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
    Mgr = GoSdk_MsgHandler.MsgManager(GoSdk, system, dataset)

    #Set data handler which spawns a worker thread to recieve input data
    Mgr.SetDataHandler(RECEIVE_TIMEOUT, ReceiveData)

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


