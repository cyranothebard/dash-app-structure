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
from components import create_profile_image_card, NumberFactAIO
from utils import GoSdk_MsgHandler
from utils.data_sensorarray import ReceiveData, groupby_and_export, map_id_to_name

##LMI internal Python script

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

def map_id_to_name(id_value):
    """
    Defines measurement names in a dictionary that can be mapped to raw data output by ID.

    """
    featurename_dict = {
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
    return featurename_dict.get(id_value, 'Unknown')

def groupby_and_export(df, output_path=None, s3_bucket=None):
    """
    Groups a DataFrame by the specified column and calculates mean values.
    Optionally exports the result to a CSV file or an AWS S3 bucket.

    Args:
        df (pd.DataFrame): Input DataFrame.
        output_path (str, optional): Local path to save the CSV file (if provided).
        s3_bucket (str, optional): AWS S3 bucket name (if provided).

    Returns:
        pd.DataFrame: Resulting DataFrame with mean values.
    # """
    # convert 'ID' and 'FeatureName' cols to str for aggregation
    df['ID'] = df['ID'].apply(str)
    df['FeatureName'] = df['FeatureName'].apply(str)
    grouped_df = df.groupby(['ID', 'FeatureName']).agg(
        {'Decision': 'mean', 'Value': 'mean', 'TimeStamp': 'mean'}).reset_index() 
    # convert 'ID' back to int and remap feature names
    grouped_df['ID'] = grouped_df['ID'].apply(int)
    grouped_df['FeatureName'] = grouped_df['ID'].map(map_id_to_name)   

    print('grouped_df:', grouped_df)
    
    # Export to CSV file (if output_path is provided)
    if output_path:
        grouped_df.to_csv(output_path, index=False)
        print(f"Saved result to {output_path}")

    # Upload to AWS S3 bucket (if s3_bucket is provided)
    if s3_bucket:
        s3_resource = boto3.resource("s3")
        data = grouped_df #BytesIO()
        grouped_df.to_csv(data, index=False)
        s3_resource.Object(s3_bucket, "grouped_data.csv").put(Body=data.getvalue())
        print(f"Uploaded result to S3 bucket: {s3_bucket}/grouped_data.csv")

    return grouped_df

def ReceiveData(dataset):
    # create dataframe to organize data
    measurement_data = pd.DataFrame(columns=['ID', 'Value', 'Decision', 'FeatureName', 'TimeStamp'])
    measurement_data_batch = pd.DataFrame(columns=['ID', 'Value', 'Decision', 'FeatureName', 'TimeStamp'])
    ## loop through all items in result message
    for i in range(GoSdk.GoDataSet_Count(dataset)):
        k_object_address = GoSdk.GoDataSet_At(dataset, i)
        dataObj = GoDataMsg(k_object_address)

        ## Retrieve stamp message
        if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_STAMP:
            stampMsg = dataObj
            msgCount = GoSdk.GoStampMsg_Count(stampMsg)
            
            for k in range(msgCount):
                stampDataPtr = GoSdk.GoStampMsg_At(stampMsg,k)
                stampData = stampDataPtr.contents
                print("frame index: ", stampData.frameIndex)
                print("time stamp: ", stampData.timestamp)
                print("encoder: ", stampData.encoder)
                print("sensor ID: ", stampData.id)
                print()
        if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_MEASUREMENT:
            measurementMsg = dataObj
            msgCount = GoSdk.GoMeasurementMsg_Count(measurementMsg)
            print("Measurement Message batch count: %d" % msgCount)

            for k in range(GoSdk.GoMeasurementMsg_Count(measurementMsg)):
                measurementDataPtr = (GoSdk.GoMeasurementMsg_At(measurementMsg, k))
                measurementData = measurementDataPtr.contents #(measurementDataPtr, POINTER(GoMeasurementData)).contents
                measurementID = (GoSdk.GoMeasurementMsg_Id(measurementMsg))
                measurement_data_agg = [{'ID': measurementID, 'Value': measurementData.numericVal, 'Decision': measurementData.decision, 
                                         'FeatureName': pd.Series(measurementID).map(map_id_to_name), 'TimeStamp': pd.to_datetime('now')}]
                measurement_data = pd.concat([measurement_data, pd.DataFrame(measurement_data_agg)], ignore_index=True)
            # print('measurement_data_batch:')
            measurement_data_batch = pd.concat([measurement_data_batch, pd.DataFrame(measurement_data)], ignore_index=True)
                # print(measurement_data)
                # print()
                # print("Measurement ID: ", measurementID)
                # print("Measurement Value: ", measurementData.numericVal)
                # print("Measurment Decision: " + str(measurementData.decision))
                # print()
            
            # print(measurement_data)
        elif GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_UNIFORM_SURFACE:
            surfaceMsg = dataObj
            print("Surface Message")

            #resolutions and offsets (cast to mm)
            XResolution = float((GoSdk.GoUniformSurfaceMsg_XResolution(surfaceMsg)))/1000000.0
            YResolution = float((GoSdk.GoUniformSurfaceMsg_YResolution(surfaceMsg)))/1000000.0
            ZResolution = float((GoSdk.GoUniformSurfaceMsg_ZResolution(surfaceMsg)))/1000000.0
            XOffset = float((GoSdk.GoUniformSurfaceMsg_XOffset(surfaceMsg)))/1000.0
            YOffset = float((GoSdk.GoUniformSurfaceMsg_YOffset(surfaceMsg)))/1000.0
            ZOffset = float((GoSdk.GoUniformSurfaceMsg_ZOffset(surfaceMsg)))/1000.0
            width = GoSdk.GoUniformSurfaceMsg_Width(surfaceMsg)
            length = GoSdk.GoUniformSurfaceMsg_Length(surfaceMsg)
            size = width * length

            print("Surface data width: " + str(width))
            print("Surface data length: " + str(length))
            print("Total num points: " + str(size)) 

            #Generate Z points
            start = time.time()
            surfaceDataPtr = GoSdk.GoUniformSurfaceMsg_RowAt(surfaceMsg, 0)
            Z = np.ctypeslib.as_array(surfaceDataPtr, shape=(size,))  
            Z = Z.astype(np.double)
            #remove -32768 and replace with nan
            Z[Z==-32768] = np.nan    
            #scale to real world units (for Z only)                  
            Z = (Z * ZResolution) + ZOffset     
            print("Z array generation time: ",time.time() - start)

            #generate X points
            start = time.time()
            X = (np.asarray(range(width), dtype=np.double) * XResolution) + XOffset
            X = np.tile(X, length)
            print("X array generation time: ",time.time() - start)

            #generate Y points
            start = time.time()
            Y = (np.arange(length, dtype=np.double)* YResolution) + YOffset
            Y = np.repeat(Y, repeats=width)
            print("Y array generation time: ",time.time() - start)

            #Generate X, Y, Z array for saving
            data_3DXYZ = np.stack((X,Y,Z), axis = 1)

            # #write to file as np array (fast)
            start = time.time()
            unique_filename = str(uuid.uuid4())
            np.save(unique_filename+"XYZ"+".npy",data_3DXYZ)
            print("wrote to file "+unique_filename+ "XYZ" + ".npy")
            print("Save npy file time: ",time.time() - start)
            
            # #write to CSV (slow)
            start = time.time()
            unique_filename = str(uuid.uuid4())
            with open(unique_filename+"XYZ.csv",'w',newline='') as csvfile:
               writer = csv.writer(csvfile,delimiter=',')
               writer.writerow(["X","Y","Z"])
               writer.writerows(data_3DXYZ)
            print("wrote to file "+unique_filename + "XYZ.csv")
            print("Save CSV file time: ",time.time() - start)

            #Display the surface (it look square unless a perspective correction is done)
            image = np.reshape(Z, (-1, width))
            maxval = np.nanmax(image)
            image = (image / maxval) * 255.0
            image = image.astype(np.uint8) 
            image = cv2.resize(image, dsize=(512, 512), interpolation=cv2.INTER_CUBIC)         
            cv2.imshow("image", image)
            cv2.waitKey(0)
            print()

        elif GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_SURFACE_INTENSITY:
            print("Intensity Message")
            surfaceIntensityMsg = dataObj

            #resolutions and offsets (cast to mm)
            XResolution = float((GoSdk.GoSurfaceIntensityMsg_XResolution(surfaceIntensityMsg)))/1000000.0
            YResolution = float((GoSdk.GoSurfaceIntensityMsg_YResolution(surfaceIntensityMsg)))/1000000.0
            XOffset = float((GoSdk.GoSurfaceIntensityMsg_XOffset(surfaceIntensityMsg)))/1000.0
            YOffset = float((GoSdk.GoSurfaceIntensityMsg_YOffset(surfaceIntensityMsg)))/1000.0
            width = GoSdk.GoSurfaceIntensityMsg_Width(surfaceIntensityMsg)
            length = GoSdk.GoSurfaceIntensityMsg_Length(surfaceIntensityMsg)
            size = width * length
            
            print("Surface data width: " + str(width))
            print("Surface data length: " + str(length))
            print("Total num points: " + str(size)) 

            #Generate I points
            surfaceIntensityDataPtr = GoSdk.GoSurfaceIntensityMsg_RowAt(surfaceIntensityMsg, 0)
            I = np.array((surfaceIntensityDataPtr[0:width*length]), dtype=np.uint8)
            
            #generate X points
            start = time.time()
            X = (np.asarray(range(width), dtype=np.double) * XResolution) + XOffset
            X = np.tile(X, length)
            print("X array generation time: ",time.time() - start)

            #generate Y points
            start = time.time()
            Y = (np.arange(length, dtype=np.double)* YResolution) + YOffset
            Y = np.repeat(Y, repeats=width)
            print("Y array generation time: ",time.time() - start)

            #Generate X, Y, Z array for saving
            data_3DXYI = np.stack((X,Y,I), axis = 1)                

            # write to file as np array (fast)
            start = time.time()
            unique_filename = str(uuid.uuid4())
            np.save(unique_filename+"XYI"+".npy",data_3DXYI)
            print("wrote to file "+unique_filename+ "XYI" + ".npy")
            print("Save npy file time: ",time.time() - start)
            
            # write to CSV (slow)
            start = time.time()
            unique_filename = str(uuid.uuid4())
            with open(unique_filename+"XYI.csv",'w',newline='') as csvfile:
               writer = csv.writer(csvfile,delimiter=',')
               writer.writerow(["X","Y","I"])
               writer.writerows(data_3DXYZ)
            print("wrote to file "+unique_filename + "XYI.csv")
            print("Save CSV file time: ",time.time() - start)

            # Display the surface (it look square unless a perspective correction is done)
            image = np.reshape(I, (-1, width))
            maxval = np.nanmax(image)
            image = (image / maxval) * 255.0
            image = image.astype(np.uint8) 
            image = cv2.resize(image, dsize=(512, 512), interpolation=cv2.INTER_CUBIC)         
            cv2.imshow("image", image)
            cv2.waitKey(0)
            print()

        elif GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_UNIFORM_PROFILE:
            print("Profile Message")
            profileMsg = dataObj

            for k in range(GoSdk.GoResampledProfileMsg_Count(profileMsg)):
                #resolutions and offsets (cast to mm)
                XResolution = float((GoSdk.GoResampledProfileMsg_XResolution(profileMsg)))/1000000.0
                ZResolution = float((GoSdk.GoResampledProfileMsg_ZResolution(profileMsg)))/1000000.0
                XOffset = float((GoSdk.GoResampledProfileMsg_XOffset(profileMsg)))/1000.0
                ZOffset = float((GoSdk.GoResampledProfileMsg_ZOffset(profileMsg)))/1000.0
                width = GoSdk.GoProfileMsg_Width(profileMsg)
                size = width

                #Generate Z points
                start = time.time()
                profileDataPtr = GoSdk.GoResampledProfileMsg_At(profileMsg, k)
                Z = np.ctypeslib.as_array(profileDataPtr, shape=(size,))
                Z = Z.astype(np.double)
                Z[Z==-32768] = np.nan                 
                Z = (Z * ZResolution) + ZOffset     
                print("Z array generation time: ",time.time() - start)

                #generate X points
                start = time.time()
                X = (np.asarray(range(width), dtype=np.double) * XResolution) + XOffset
                print("X array generation time: ",time.time() - start)

                #Generate X, Y, Z array for saving
                data_3DXZ = np.stack((X,Z), axis = 1)   

                #write to file as np array (fast)
                unique_filename = str(uuid.uuid4())
                np.save(unique_filename+"XZ"+".npy",data_3DXZ)
                
                #write to CSV (slow)
                unique_filename = str(uuid.uuid4())
                with open(unique_filename+"XZ.csv",'w',newline='') as csvfile:
                   writer = csv.writer(csvfile,delimiter=',')
                   writer.writerow(["X","Z"])
                   writer.writerows(data_3DXZ)
                print("wrote to file "+unique_filename)
                
                print()
    print('Measurement Data, batch:', measurement_data_batch)
    grouped_df = groupby_and_export(measurement_data_batch)
    print('grouped_df:', grouped_df)
    kObject_Destroy(dataset)
    return grouped_df, # measurement_data_batch


df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/c78bf172206ce24f77d6363a2d754b59/raw/c353e8ef842413cae56ae3920b8fd78468aa4cb2/usa-agricultural-exports-2011.csv')
cwd = os.getcwd()
order_data_path = os.path.join(cwd, 'src', 'assets', 'data', 'RPS Example Data 1.csv')
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
    # return html.Table([
    #     html.Thead(
    #         html.Tr([html.Th(col) for col in dataframe.columns])
    #     ),
    #     html.Tbody([
    #         html.Tr([
    #             html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
    #         ]) for i in range(min(len(dataframe), max_rows))
    #     ])
    # ])
    dataframe = ReceiveData()
    return dash_table.DataTable(
        data=dataframe.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in dataframe.columns],
        style_data_conditional = sensor_data_conditional
    )
    
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
        # DEBUGGING attempt to fix image loading issue with alternate technique
        # html.Div(html.Img(src=app.get_asset_url('side_profiles/70E100_left.png'), style={'height':'50%', 'width':'30%', 'padding':'10px','textAlign':'left', 'align':'left', 'class':'column'})),
        # html.Div(html.Img(src=app.get_asset_url('side_profiles/70E100_right.png'), style={'height':'50%', 'width':'30%', 'padding':'10px', 'textAlign':'right', 'align':'right', 'class':'column'})),
        dbc.Row(
            [
                create_profile_image_card('70E100', 'left'), # DEBUGGING - function results in broken images
                create_profile_image_card('70E100', 'right')
            ]
        ),
        html.H3('Measurement Data'),
        generate_table(ReceiveData),
        # generate_table(df_sensor_sample),
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


