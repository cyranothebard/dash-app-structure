##LMI internal Python script

from asyncio.windows_events import NULL
import os
import ctypes
from ctypes import *
from array import *
import csv
import numpy as np
from PIL import Image, ImageDraw
import GoSdk_MsgHandler
import uuid
import cv2
import time

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

def RecieveData(dataset):
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
            print("Measurement Message batch count: %d" % msgCount);

            for k in range(GoSdk.GoMeasurementMsg_Count(measurementMsg)):
                measurementDataPtr = (GoSdk.GoMeasurementMsg_At(measurementMsg, k))
                measurementData = measurementDataPtr.contents #(measurementDataPtr, POINTER(GoMeasurementData)).contents
                measurementID = (GoSdk.GoMeasurementMsg_Id(measurementMsg))
                print("Measurement ID: ", measurementID)
                print("Measurement Value: ", measurementData.numericVal)
                print("Measurment Decision: " + str(measurementData.decision))
                print()
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
            # start = time.time()
            # unique_filename = str(uuid.uuid4())
            # np.save(unique_filename+"XYZ"+".npy",data_3DXYZ)
            # print("wrote to file "+unique_filename+ "XYZ" + ".npy")
            # print("Save npy file time: ",time.time() - start)
            
            # #write to CSV (slow)
            # start = time.time()
            # unique_filename = str(uuid.uuid4())
            # with open(unique_filename+"XYZ.csv",'w',newline='') as csvfile:
            #    writer = csv.writer(csvfile,delimiter=',')
            #    writer.writerow(["X","Y","Z"])
            #    writer.writerows(data_3DXYZ)
            # print("wrote to file "+unique_filename + "XYZ.csv")
            # print("Save CSV file time: ",time.time() - start)

            #Display the surface (it look square unless a perspective correction is done)
            # image = np.reshape(Z, (-1, width))
            # maxval = np.nanmax(image)
            # image = (image / maxval) * 255.0
            # image = image.astype(np.uint8) 
            # image = cv2.resize(image, dsize=(512, 512), interpolation=cv2.INTER_CUBIC)         
            # cv2.imshow("image", image)
            # cv2.waitKey(0)
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

            #write to file as np array (fast)
            #start = time.time()
            #unique_filename = str(uuid.uuid4())
            #np.save(unique_filename+"XYI"+".npy",data_3DXYI)
            #print("wrote to file "+unique_filename+ "XYI" + ".npy")
            #print("Save npy file time: ",time.time() - start)
            
            #write to CSV (slow)
            #start = time.time()
            #unique_filename = str(uuid.uuid4())
            #with open(unique_filename+"XYI.csv",'w',newline='') as csvfile:
            #    writer = csv.writer(csvfile,delimiter=',')
            #    writer.writerow(["X","Y","I"])
            #    writer.writerows(data_3DXYZ)
            #print("wrote to file "+unique_filename + "XYI.csv")
            #print("Save CSV file time: ",time.time() - start)

            # Display the surface (it look square unless a perspective correction is done)
            # image = np.reshape(I, (-1, width))
            # maxval = np.nanmax(image)
            # image = (image / maxval) * 255.0
            # image = image.astype(np.uint8) 
            # image = cv2.resize(image, dsize=(512, 512), interpolation=cv2.INTER_CUBIC)         
            # cv2.imshow("image", image)
            # cv2.waitKey(0)
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
                #unique_filename = str(uuid.uuid4())
                #np.save(unique_filename+"XZ"+".npy",data_3DXZ)
                
                #write to CSV (slow)
                #unique_filename = str(uuid.uuid4())
                #with open(unique_filename+"XZ.csv",'w',newline='') as csvfile:
                #    writer = csv.writer(csvfile,delimiter=',')
                #    writer.writerow(["X","Z"])
                #    writer.writerows(data_3DXZ)
                #print("wrote to file "+unique_filename)
                
                print()

    kObject_Destroy(dataset)

# if __name__ == "__main__":
#     # Instantiate system objects
#     api = kAssembly(kNULL)
#     system = GoSystem(kNULL)
#     sensor = GoSensor(kNULL)
#     dataset = GoDataSet(kNULL)
#     dataObj = GoDataMsg(kNULL)
#     changed = kBool(kNULL)

#     print('Sdk Version is: ' + getVersionStr())

#     GoSdk.GoSdk_Construct(byref(api))  # Build API
#     GoSdk.GoSystem_Construct(byref(system), kNULL)  # Construct sensor system

#     #connect to sensor via IP
#     sensor_IP = b"127.0.0.1" #default for local emulator is 127.0.0.1
#     top_sensor_IP = b'192.168.92.107'
#     ipAddr_ref = kIpAddress()
#     kApi.kIpAddress_Parse(byref(ipAddr_ref), sensor_IP)
#     GoSdk.GoSystem_FindSensorByIpAddress(system,byref(ipAddr_ref),byref(sensor))
    
#     #connect to sensor via ID
#     #sensor_ID = 54384
#     #GoSdk.GoSystem_FindSensorById(system, sensor_ID, byref(sensor))

#     GoSdk.GoSensor_Connect(sensor)  # Connect to the sensor
#     GoSdk.GoSystem_EnableData(system, kTRUE)  # Enable the sensor's data channel to receive measurement data
#     #GoSdk.GoSensor_Start(sensor)  # Start the sensor to gather data
#     print("connected!")

#     #Initialize message handler manager
#     Mgr = GoSdk_MsgHandler.MsgManager(GoSdk, system, dataset)

#     #Set data handler which spawns a worker thread to recieve input data
#     Mgr.SetDataHandler(RECEIVE_TIMEOUT, RecieveData)

#     #Issue a stop then start incase the emulator is still running. For live sensors, only a start is needed.
#     GoSdk.GoSensor_Stop(sensor) 
#     GoSdk.GoSensor_Start(sensor)
    
#     #Do nothing
#     while(input() != "exit"):
#         pass
    
#     #Can close thread manually by recalling data handler with kNull passed
#     #Mgr.SetDataHandler(GoSdk, system, dataset, RECEIVE_TIMEOUT, kNULL)


#     ### Destroy the system object and api
#     kObject_Destroy(system)
#     kObject_Destroy(api)


