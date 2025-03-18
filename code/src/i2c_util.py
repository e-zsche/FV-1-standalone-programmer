from machine import Pin, I2C
import time

wp = Pin(14)
wp.on()
i2c = I2C(0, scl=Pin(13), sda=Pin(12))

def write_eeprom(mem_addr, vals):
    # page write
    page_size = 32
    n_slices = int(len(vals)/32)
    print(f"total len: len(vals)\nnum of slices: {n_slices}")
    for i in range(n_slices):
        start_index = i*page_size
        end_index = start_index + page_size
        mem_offs = mem_addr + start_index
        buf = vals[start_index:end_index]
        print(f"write {len(buf)} bytes to addr: {mem_offs}\n{buf}")
        wp.off()
        i2c.writeto_mem(0x50, mem_offs, buf, addrsize=16)
        wp.on()
        time.sleep(0.005)

    #i+=1
    #n = i2c.writeto_mem(0x50, i*32, vals[i*32:], addrsize=16)
    #print(f"addr {i*32} wrote slice {i}: {n} bytes")

def read_eeprom(mem_addr, num_bytes):
    return i2c.readfrom_mem(0x50, mem_addr, num_bytes, addrsize=16)

def do_scan():
    print('Scan i2c bus...')
    devices = i2c.scan()

    if len(devices) == 0:
        print("No i2c device !")
    else:
        print('i2c devices found:',len(devices))

        for device in devices:
            print("address: ",hex(device))
