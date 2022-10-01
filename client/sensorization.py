from datetime import Datetime
import socket
import binascii
import struct
import time
import config
import machine
import ujson
import json
import pycom
import lora
import tfmini
import acelerometro
from machine import I2C
import urtc
import webserver
from math import sqrt
from machine import Pin
from uos import remove
import utime
import datetime
import _thread



HISTORY_FILE = "hits.txt"
INSIDE_PIN = 'P21'
HIT_PIN = 'P22'
COMMUNICATION_EVERY_SECONDS = 5

class Sensorization():
    # vars
    alt_sensor, acel_sensor = "alt", "accl"
    inside, hit = "ins", "hit"
    gps = "gps"

    # History
    lenHistorial = None
    posicionHistorial = None
    historial = None
    counter = None

    # RTC
    rtc_instance = None

    # Acel
    accel_instance = None
    accel_recv = None
    accel_calc = None
    accel_x, accel_y, accel_z = None, None, None
    in_hit = None
    register_hit = None
    current_accel = None

    # Dist
    dist_instance = None
    dist_recv = None
    
    
    # Thresholds
    thresholds = {
        alt_sensor: None,
        acel_sensor: None
    }
    
    # Scoket
    conn = None
    
    # Sensors
    sensors = {
        alt_sensor: None,
        acel_sensor: None,
        gps: None
    }

    # Actuators
    relays = {
        inside: None,
        hit: None
    }
    hit_relay = None
    reset_hit = None
    inside_relay = None


     
    def __init__(self):
        # Initialize LoRa connection.
        self.conn = lora.Lora()

        # Reset mem values
        if pycom.nvs_get("techo") == None:
            pycom.nvs_set("techo", 0)
        if pycom.nvs_get("aceleracion") == None:
            pycom.nvs_set("aceleracion", 0)
        if pycom.nvs_get("golpe") == None:
            pycom.nvs_set("golpe", 0)

        # Thresholds
        self.thresholds[self.alt_sensor] = pycom.nvs_get("techo")
        self.thresholds[self.acel_sensor] = pycom.nvs_get("aceleracion")

        # hit value
        self.hit_relay = pycom.nvs_get("golpe")

        print("Valores iniciales. LIMITE_TECHO: {0}, LIMITE_ACELERACIÓN: {1}, GOLPE_LED: {2}".format(self.thresholds[self.alt_sensor], self.thresholds[self.acel_sensor], self.hit_relay))
        # Send initial values through LoRa
        data = '{"th_alt": %d, "th_hit": %d}' % (self.thresholds[self.alt_sensor],self.thresholds[self.acel_sensor])
        print(data)
        self.conn.sendData(data)
        time.sleep(4)

        # Initialize LED pins
        self.inside_relay = Pin(INSIDE_PIN, mode=Pin.OUT)
        self.hit_relay = Pin(HIT_PIN, mode=Pin.OUT)


        # ----------------- Initialize Sensors ------------------ 
        # Lidar sensor
        try:
            self.dist_instance = tfmini.Tfmini()
        except: print("Lidar initialization fail!")
        self.relays[self.inside] = 0
        self.sensors[self.alt_sensor] = 0.0

        
        # Ubication
        self.sensors[self.gps] = [0.0, 0.0]
        # RTC
        i2c_port = I2C(0, I2C.MASTER)
        self.rtc_instance = urtc.PCF8523(i2c_port)
        # Accel
        self.accel_instance = acelerometro.Acelerometro()
        self.in_hit = False
        self.relays[self.hit] = 0 
        self.register_hit = False
        self.reset_hit = False
        self.current_accel = 0.0
        self.accel_calc = 0.0
        self.counter = 0
        self.accel_x, self.accel_y, self.accel_z = 0.0, 0.0, 0.0
        self.sensors[self.acel_sensor] = 0.0

        # ----------------- End Initialize Sensors ------------------ 

        # Load history
        self.lenHistorial = 20
        self.posicionHistorial = 0
        self.historial = []
        print("------------------------------------")
        print("Rebuilding historic...")
        print("------------------------------------")
        # self.rebuildHistoric("hits.txt") # Uncoment
        print("rebuild done, got {} entries".format(len(self.historial)))
        print("------------------------------------")
        print("\n")

        # Webserver initialization
        webserver.principal = self

    


    def communication(self):
        print("------------------------------------")
        print("RECEPCIÓN DE DATOS")
        print("------------------------------------")
        # Receive data from Server
        self.receive_state()
        print("------------------------------------")
    
        print("------------------------------------")
        print("ENVÍO DE DATOS")
        print("------------------------------------")
        # Send data to Server
        self.send_current_state()
        print("------------------------------------")
        print("\n")


    def check_sensors(self,data):
        while True:
            time.sleep(0.2)
            self.check_accel_sensor()
            self.check_lidar_sensor()
            self.manage_state()


    def start(self): # change name to start
        
        _thread.start_new_thread(self.check_sensors, (None,))
        
        # Create a timed loop
        start_time = time.time()

        while True:
            #time.sleep(0.5) # Comentar después de las pruebas
            current_time = time.time()
            elapsed_time = current_time - start_time


            if elapsed_time > COMMUNICATION_EVERY_SECONDS:
                self.communication()
                # Rst time
                start_time = time.time()
    
        
    def manage_state(self): 
        # Check if the reset hit has been pressed
        if self.reset_hit:
            # Reset hit
            print("Resetting hit...")
            self.reset_hit_procedure()


        # Dist sensor
        if self.dist_recv < self.thresholds[self.alt_sensor]:
            self.inside_relay(True)
            self.relays[self.inside] = 1
            print("LED INTERIOR ACTIVO!") # comentar cuando el LED funcione
        else: 
            self.inside_relay(False)
            self.relays[self.inside] = 0
            print("LED INTERIOR NO ACTIVO")

        # -------------------- Accel sensor --------------------
    
        if self.accel_calc > self.thresholds[self.acel_sensor]:
            # Hit detected
            if not self.in_hit:
                # Hit detected right now
                self.in_hit, self.register_hit = True, True
                self.current_accel = self.accel_calc
            else:
                if self.current_accel > self.accel_calc:
                    # Incrementing accelerometer value
                    self.current_accel = self.accel_calc
        

        if self.register_hit: # Hit detected, that needs to be registered
            
            print("Hit detected with accel of ", self.accel_calc)
            self.hit_relay(True)
            self.relays[self.hit] = 1

            # Set datetime 
            date = self.rtc_instance.datetime()
     
            #self.add_entry_historic(self.accel_calc, date) # Log del golpe

            self.add_entry_historic(self.accel_calc, date, "{:02d}/{:02d}/{} {:02d}:{:02d}:{:02d}".format(date.day,date.month,date.year,date.hour,date.minute,date.second)) # Log del golpe
            self.register_hit = False 
            webserver.sendHit(date, self.accel_calc) # Prueba
            if not self.hit_relay:
                print("Activating hit LED")
                self.hit_relay(True) 
                pycom.nvs_set("golpe", 1)

        # -------------------- End Accel sensor --------------------
        # Send to webserver (optional)
        webserver.sendData(self.sensors[self.alt_sensor], self.sensors[self.acel_sensor])


    def check_lidar_sensor(self):
        try: 
            # Read data from lidar sensor
            self.dist_recv = self.dist_instance.lee()
            self.dist_recv = float(self.dist_recv / 100)
            self.sensors[self.alt_sensor] = self.dist_recv
            print("Dist sensor. Data read: ", self.dist_recv)
        except:
            print("Sensor error: check_lidar_sensor")


    def check_accel_sensor(self):
        try:
            # Lee datos del sensor de aceleración y los almacena en una tupla de enteros
            (self.accel_recv, self.accel_x, self.accel_y, self.accel_z) = self.accel_instance.lee()
            # Setting value of sensor
            self.accel_calc = sqrt(self.accel_recv)
            self.sensors[self.acel_sensor] = self.accel_calc
            print("Accel sensor. Data read: x:{0}, y:{1}, z:{2}, g:{3}".format(self.accel_x,self.accel_y,self.accel_z, self.accel_calc))
        except:
            print("Sensor error: check_accel_sensor")
        

    # We need a function to read the sensors in real time and activate the pertinent relay.
    def send_current_state(self):
        
        # Prepare to send
        #data = '{"contador": %d, "uptime": %d, "golpe": %d, "interior": %d, "data": { "x": %f, "y": %f, "z": %f, "total": %f  }, "gnss": { "lat": %f,  "long": %f } }' % (self.counter, time.time(), self.hit, self.inside, self.accel_x, self.accel_y, self.accel_z, self.accel_calc, self.sensors[self.gps][0], self.sensors[self.gps][1])
        # Convert altitude from cm to m
        # alt_value = self.sensors[self.alt_sensor] / 100
        data = '{"upt": %d, "hit": %d, "ins": %d, "alt":%.2f, "x": %.2f, "y": %.2f, "z": %.2f, "t": %.2f}' % (time.time(), self.relays[self.hit], self.relays[self.inside], self.sensors[self.alt_sensor], self.accel_x, self.accel_y, self.accel_z, self.accel_calc)
        self.counter = (self.counter+1)%1000
        
        # Call send function with the state 
        #data = ujson.dumps(data) # use only when data is a dictionary
        self.conn.sendData(data)
        print("Data sent (counter: {0}): {1}".format(self.counter,data))
        
        # Sending to webserver
        webserver.sendData(self.sensors[self.alt_sensor], self.sensors[self.acel_sensor])
        time.sleep_ms(10)

        #log
        print("Estado actual sensor de altura: {}".format(self.sensors[self.alt_sensor]))
        print("Estado actual sensor de golpes: {}".format(self.sensors[self.acel_sensor]))

    


    def receive_state(self):
        # Call recv function and charge the result to a thresholds dictionary.
        rx = self.conn.receiveData()
        changes = False
        if rx:
            try:
                # Convert bytes to a dictionary String and the result is put it in a dictionary
                data  = json.loads(rx.decode("utf-8"))
                recv_thresholds = None
                recv_relays = None
                if 'th' in data:  
                    recv_thresholds = data['th']
                if 'rel' in data:
                    recv_relays = data['rel']

                # If data is not equal to old thresholds
                if recv_thresholds != None:
                    print("Setting thresholds...")  
                    # Save data to mem
                    if self.alt_sensor in recv_thresholds and recv_thresholds[self.alt_sensor] != self.thresholds[self.alt_sensor]:
                        self.thresholds[self.alt_sensor] = data['th'][self.alt_sensor]
                        pycom.nvs_set("techo", self.thresholds[self.alt_sensor])
                        changes = True
                        

                    if self.acel_sensor in recv_thresholds and recv_thresholds[self.acel_sensor] != self.thresholds[self.acel_sensor]:    
                        self.thresholds[self.acel_sensor] = data['th'][self.acel_sensor]
                        pycom.nvs_set("aceleracion", self.thresholds[self.acel_sensor])
                        changes = True
                
                if recv_relays != None:
                    print("Setting relays...")
                    if self.inside in recv_relays:
                        self.relays[self.inside] = recv_relays[self.inside]
                        self.inside_relay(bool(self.relays[self.inside]))
                        changes = True
                    if self.hit in recv_relays:
                        self.relays[self.hit] = recv_relays[self.hit]
                        self.hit_relay(bool(self.relays[self.hit]))
                        pycom.nvs_set("golpe", self.relays[self.hit])
                        changes = True

                if changes:
                    # Send initial values through LoRa
                    data = '{"th_alt": %d, "th_hit": %d, "hit": %d, "ins": %d}' % (self.thresholds[self.alt_sensor],self.thresholds[self.acel_sensor], self.relays[self.hit], self.relays[self.inside])
                    self.conn.sendData(data)
                    time.sleep(4)

            except Exception as e:
                print("Error: ", str(e))
                print('Error al establecer parámetros. Sintaxis de envío: {"th":{"alt":0, "accl":0}, "rel":{"hit":0, "ins":0}}')
                self.thresholds[self.alt_sensor] = pycom.nvs_get("techo")
                self.thresholds[self.acel_sensor] = pycom.nvs_get("aceleracion")


        #log
        print("------------------------------------")
        print("LÍMITES ACTUALES")
        print("Umbral de altura: {}".format(self.thresholds[self.alt_sensor]))
        print("Umbral de golpes: {}".format(self.thresholds[self.acel_sensor]))
        print("------------------------------------")
     
        
      
    # Se resetea el golpe
    def reset_hit_procedure(self):
        self.relays[self.hit] = 0
        self.reset_hit = False
        self.register_hit = False
        self.in_hit = False
        # Desactiva el LED inicador de golpe
        self.hit_relay(False)
        # Historial de golpes
        self.historial = []
        # Borra el fichero de registros 
        remove(HISTORY_FILE)
        # Setea el valor de memoria a 0
        pycom.nvs_set("golpe", 0) # Puede interesar eliminarlo para evitar el reset del golpe en caso de desconectar el suministro eléctrico

    #Añade un nuevo golpe al histórico
    def add_entry_historic(self, fuerza, date, tiempo, write=True):
        self.historial.append({"date": tiempo, "accel": fuerza})
        if len(self.historial) > self.lenHistorial:
            self.historial = self.historial[1:]
        webserver.sendHit(tiempo, fuerza)

        if write:
            try:
                f = open("hits.txt", 'a+')
                f.write("{};{}\n".format(tiempo, fuerza))
                f.close()
            except:
                print("cannot write to file")
            
            # self.send_current_state() # Ahora se hace en el loop()
        
        # Send hit through LoRa

        print(tiempo)

        timestamp = Datetime().timestamp(date.year, date.month, date.day, date.hour, date.minute, date.second)
        data = '{"datetime": %d, "hit_value": %.2f}' % ((timestamp * 1000),fuerza)
        self.conn.sendData(data)
        print(data)
        time.sleep(4)

    
    # rebuildHistoric coge los datos que hay en fichero y los mete en historial actual
    def rebuildHistoric(self, f_name):
        try:
            f = open(f_name, 'r')
        except:
            print("no file for old data")
            return
        
        data = f.readlines()
        if len(data) > self.lenHistorial:
            data = data[-self.lenHistorial:]
        for d in data:
            d = d[:-1]
            print(d)
            flAccel = None
            try:
                fields = d.split(";")
                date, accel = fields[0], fields[1]
            except Exception as e:
                print("error parsing ", e)
                continue
            try:
                flAccel = float(accel)
                
            except:
                print("error converting acceleration")
            self.add_entry_historic(flAccel, date, write=False)
        f.close()
    

    # ------------------------ FOR WEBSERVER --------------------------
    def getValues():
        return "hola"

    def update_thresholds(self, height, accel):
        try:
            # Cálculo del cuadrado del límite de aceleración
            self.thresholds[self.acel_sensor] = int(accel) # REVISAR!
 
            # Multiplica el límite de techo por 100
            self.thresholds[self.alt_sensor] = int(float(height) * 100)
        except:
            print("wrong type on update")
    
        # Guardado en memoria de los límites
        pycom.nvs_set("aceleracion", self.thresholds[self.acel_sensor])
        pycom.nvs_set("techo", self.thresholds[self.alt_sensor])
 
    # ------------------------ END FOR WEBSERVER --------------------------  

