#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#


""" LoPy LoRaWAN Nano Gateway example usage """

import config
from nanogateway import NanoGateway
import binascii
from network import LoRa
from network import WLAN;
import machine
from binascii import hexlify
import network


print()

lora = LoRa()
print("Device EUI (LoRa): %s" % (binascii.hexlify(lora.mac()).decode('ascii')))
wlan = WLAN() 
print("WLAN EUI: %s" % (binascii.hexlify(machine.unique_id()).decode('ascii')))



if __name__ == '__main__':
    nanogw = NanoGateway(
        id=config.GATEWAY_ID,
        frequency=config.LORA_FREQUENCY,
        datarate=config.LORA_GW_DR,
        ssid=config.WIFI_SSID,
        password=config.WIFI_PASS,
        server=config.SERVER,
        port=config.PORT,
        ntp_server=config.NTP,
        ntp_period=config.NTP_PERIOD_S
        )

    nanogw.start()
    nanogw._log('You may now press ENTER to enter the REPL')
    input()