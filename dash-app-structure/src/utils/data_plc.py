# required imports
from PyPlcnextRsc import Device, RscVariant, RscType
from PyPlcnextRsc.Arp.Plc.Gds.Services import IDataAccessService, WriteItem

# we have to login using the standard credentials
# it is not recomended to store the login data in code
# the following example should only show how to interact with the process data
secureInfoSupplier = lambda:("admin","password")

# login to the device
device = Device('127.0.0.1', secureInfoSupplier=secureInfoSupplier)
device.connect()

# service to access the process data
data_access_service = IDataAccessService(device)

# read one variable
read_item = data_access_service.ReadSingle("Arp.Plc.Eclr/test_in2")

# read multiple variables
read_items = data_access_service.Read(("Arp.Plc.Eclr/loaddate", "Arp.Plc.Eclr/uniqueid", "Arp.Plc.Eclr/workorder",
                                       "Arp.Plc.Eclr/length", "Arp.Plc.Eclr/width", "Arp.Plc.Eclr/color",
                                       "Arp.Plc.Eclr/itemdescription"))
loaddate = read_items[0]
uniqueid = read_items[1]
workorder = read_items[2]
length = read_items[3]
width = read_items[4]
color = read_items[5]
itemdescription = read_items[6]

# get the value of the read_item
value = read_item.Value.GetValue()
# get the data type of the read_item
value = read_item.Value.GetType()

# first create the variable containing the value and the data type
rscv = RscVariant(16,RscType.Int16)
# create a WriteItem with the destination process variable
wi = WriteItem("Arp.Plc.Eclr/MainInstance.test_in3", rscv)
wi1 = 'test'
wi2 = 'test2'
# write single process variable
data_access_service.WriteSingle(wi)

# write several process variables
data_access_service.Write((wi1, wi2,))