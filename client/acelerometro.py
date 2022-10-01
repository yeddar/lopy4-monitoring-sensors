from machine import I2C
import time


class Acelerometro():
    i2c = None

    def __init__(self):
        self.i2c = I2C(I2C.MASTER)
        # 0x0A es la dirección del acelerómetro
        dato1 = (0x22, 3)
        dato2 = (0x20, 0)
        while(int.from_bytes(self.i2c.readfrom_mem(0x0A, dato1[0], 1), "Big") != dato1[1]):
             print(self.i2c.writeto_mem(0x0A, dato1[0], dato1[1]))

        while(int.from_bytes(self.i2c.readfrom_mem(0x0A, dato2[0], 1), "Big") != dato2[1]):
            print(self.i2c.writeto_mem(0x0A, dato2[0], dato2[1]))

    def lee(self):
        x_data = 0
        y_data = 0
        z_data = 0

        divi = 8
        aux = self.i2c.readfrom_mem(0x0A, 0x04, 1)
        x_data = int.from_bytes(aux, "Big")
        y_data = int.from_bytes(self.i2c.readfrom_mem(0x0A, 0x06, 1), "Big")
        z_data = int.from_bytes(self.i2c.readfrom_mem(0x0A, 0x08, 1), "Big")
        if x_data < 128:
            x= (x_data/divi)
        else:
            x= ((x_data-256)/divi)
        if y_data < 128:
            y= (y_data/divi )
        else:
            y= ((y_data-256)/divi)
        if z_data < 128:
            z= (z_data/divi)
        else:
            z= ((z_data-256)/divi)
        modulo_cuadrado = x * x + y * y + z * z
        return (modulo_cuadrado,x,y,z)
        