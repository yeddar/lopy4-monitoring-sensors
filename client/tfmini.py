from machine import UART

import time
class Tfmini():
    uart = UART(1, 115200)

    def __init__(self):
        self.uart.init(115200, bits=8, parity=None, stop=1)
        buf = []
        self.uart.write(bytes(0x42))
        self.uart.write(bytes(0x57))
        self.uart.write(bytes(0x02))
        self.uart.write(bytes(0x00))
        self.uart.write(bytes(0x00))
        self.uart.write(bytes(0x00))
        self.uart.write(bytes(0x01))
        self.uart.write(bytes(0x06))
        time.sleep(0.5)

    def lee(self):
        numCharsRead = 0
        lastChar = 0x00
        # Primero hago leer bytes hasta que encuentro los que marcan el inicio de transmisión de datos (Que son los dos 0x59)
        while self.uart.any():
            curChar = int.from_bytes(self.uart.read(1), "Big")
           
            if curChar!=None:
                if (lastChar == 0x59) and (curChar == 0x59):
                    #print("Inicio de la transmisión de datos")
                    break
                else:
                    #print("Leyendo datos...")         
                    lastChar = curChar
                    numCharsRead += 1
        frame = []
        # Aunque hayan 7 bytes de datos, sólo me interesan los dos primeros
        
        for i in range(2):
            #print("lectura ",i)
            auxiliar = self.uart.read(1)
            print("Dato leído: ", auxiliar)
            if auxiliar == None:
                frame.append(0)
            else:
                frame.append(int.from_bytes(auxiliar, "Big"))
        dist = frame[1]*256 + frame[0]
        # Vacío el buffer de entrada
        while self.uart.any():
            self.uart.readline()
        return dist
