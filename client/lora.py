from network import LoRa
import socket
import binascii
import struct
import time
import config
import machine
import ujson
import json
import pycom


class Lora():
    # Scoket
    s = None

    def __init__(self):

        # initialize LoRa in LORAWAN mode.
        # Please pick the region that matches where you are using the device:
        # Asia = LoRa.AS923
        # Australia = LoRa.AU915
        # Europe = LoRa.EU868
        # United States = LoRa.US915
        lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, device_class=LoRa.CLASS_C)

        # CONEXIÓN CON OTAA
        # create an OTA authentication params
        dev_eui = binascii.unhexlify(config.DEV_EUI)
        app_eui = binascii.unhexlify(config.APP_EUI)
        app_key = binascii.unhexlify(config.APP_KEY)

        # set the 3 default channels to the same frequency (must be before sending the OTAA join request)
        lora.add_channel(0, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(1, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(2, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(3, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(4, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(5, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(6, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(7, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(8, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(9, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)
        lora.add_channel(10, frequency=config.LORA_FREQUENCY, dr_min=0, dr_max=5)


        # join a network using OTAA
        lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0, dr=config.LORA_NODE_DR)

        # wait until the module has joined the network
        while not lora.has_joined():
            time.sleep(2.5)
            print('Not joined yet...')
        print('JOINED THROUGH OTAA!')
        pycom.heartbeat(False)
       

        # remove all the non-default channels
        for i in range(3, 16):
            lora.remove_channel(i)

        # create a LoRa socket
        self.s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

        # set the LoRaWAN data rate
        # set the LoRaWAN data rate
        self.s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_NODE_DR)
        self.s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, False) # Modificar

        # make the socket non-blocking
        self.s.setblocking(False) # Modificado
    


    def sendData(self, data):
        try :
            self.s.setblocking(True)
            self.s.send(data)
            self.s.setblocking(False)
            print("Data sent successfully")
            
        except:
            print("Error sending data.")
        
    
    def receiveData(self):
        try:
            self.s.setblocking(False)
            rx = self.s.recv(256)
            self.s.setblocking(True)
            print("Data received from Gateway: ",rx)
            

        except:
            print("Error receiving data")
        
        return rx
        

