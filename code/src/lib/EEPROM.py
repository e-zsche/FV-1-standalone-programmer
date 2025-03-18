from machine import Pin, I2C
import time

class EEPROM_24LC32A():
    ADDR=0x50
    I2C_BUS_TIMEOUT = 0.005
    def __init__(self, scl, sda, wp, i2c_bus=0, freq=400000):
        self.wp = wp
        self.wp.on()
        self.i2c = I2C(i2c_bus, scl=scl, sda=sda, freq=freq)

    def read_data(self, mem_addr, num_bytes):
        return self.i2c.readfrom_mem(self.ADDR, mem_addr, num_bytes, addrsize=16)

    def write_data(self, mem_addr, data):
        if len(data) < 32:
            self.wp.off()
            self.i2c.writeto_mem(self.ADDR, mem_addr, data, addrsize=16)
            self.wp.on()
            return

        self.wp.off()
        for i in range(int(len(data)/32)):
            mem_offs = mem_addr + i*32
            start_index = i*32
            self.i2c.writeto_mem(self.ADDR, mem_offs, data[start_index:start_index+32], addrsize=16)
            time.sleep(self.I2C_BUS_TIMEOUT)
        i+=1
        mem_offs = mem_addr + i*32
        start_index = i*32
        self.i2c.writeto_mem(self.ADDR, mem_offs, data[start_index:], addrsize=16)
        self.wp.on()
