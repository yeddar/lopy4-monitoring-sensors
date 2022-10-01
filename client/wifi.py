from network import WLAN

ssid = "720tec-iot-diego"
pwd = "ioniPRim65!"

wlan = WLAN()
wlan.init(mode=WLAN.AP, ssid=ssid, auth=(WLAN.WPA2, pwd))