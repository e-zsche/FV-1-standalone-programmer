from machine import Pin, I2C
import time

wp = Pin(14, Pin.OUT)
wp.on()
i2c = I2C(0, scl=Pin(13), sda=Pin(12))

def read_eeprom(mem_addr, num_bytes):
    return i2c.readfrom_mem(0x50, mem_addr, num_bytes, addrsize=16)

def read_program(num_program):
    if num_program < 1 or num_program > 8:
        print("program number must be between 1 or 8")
        return
    return read_eeprom(0x200*(num_program-1), 0x200)

def write_eeprom(mem_addr, byte_buf):
    if len(byte_buf) < 32:
        wp.off()
        i2c.writeto_mem(0x50, mem_addr, byte_buf, addrsize=16)
        wp.on()
        return

    n_slices = int(len(byte_buf)/32)
    for i in range(n_slices):
        mem_offs = mem_addr + i*32
        wp.off()
        i2c.writeto_mem(0x50, mem_offs, byte_buf[mem_offs:mem_offs+32], addrsize=16)
        wp.on()
        time.sleep(0.005) # 5ms wait time needed by eeprom
    i+=1
    mem_offs = mem_addr + i*32
    wp.off()
    i2c.writeto_mem(0x50, mem_offs, byte_buf[mem_offs:mem_offs+32], addrsize=16)
    wp.on()

def clone_eeprom():
    print("reading from eeprom")

    if not 0x50 in i2c.scan():
        print("no eeprom found. Aborting")
        return

    if input("start cloning [y/N]").lower() not in ["y", "yes"]:
        print("Aborting")
        return

    # read all programs
    content = b""
    for i in range(8):
        content += read_eeprom(i*0x200, 0x200)
    print("read successful")

    if input("insert empty EEPROM and continue [y/N]").lower() not in ["y", "yes"]:
        print("Aborting")
        return

    write_eeprom(0, content)

    print("checking content")
    content2 = b""
    for i in range(8):
        content2 += read_eeprom(i*0x200, 0x200)

    if not content == content2:
        print("ERROR: data verification failed")
        return

    print("SUCCESS: data verified and EEPROM is cloned")

def show_content():
    doc_str = """
    available functions:
      show_content()
        show this help text

      read_eeprom(mem_addr:int, num_bytes:int) -> bytes
        reads and returns num_bytes from eeprom starting at address mem_addr

      write_eeprom(mem_addr:int, byte_buf:bytes)
        writes bytes from byte_buf to eeprom starting at address mem_addr

      read_program(num_program) -> bytes
        read FV-1 program from EEPROM. num_program must be between 1 to 8

      clone_eeprom()
        clone EEPROM content two another EEPROM
    """
    print(doc_str)

show_content()
