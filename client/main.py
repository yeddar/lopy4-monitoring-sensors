import time
import sensorization
from network import LoRa
import binascii
from binascii import hexlify
import webserver



aplora = LoRa();
print("Device EUI (LoRa): %s" % (binascii.hexlify(aplora.mac()).decode('ascii')))

sensorization_instance = sensorization.Sensorization() # Create an instance of lor class
webserver.server(sensorization_instance) # Initialize webserver

# Execute sensorization
seconds = 1
sensorization_instance.start()

        

