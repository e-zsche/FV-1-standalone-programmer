import os
import time
import uos
import gc

from machine import Pin, SPI, I2C
from micropython import const  # type: ignore
from sysfont import sysfont

from lib import asfv1
from lib.ST7735 import TFT
from lib.sdcard import SDCard
from lib import widgets
from lib.EEPROM import EEPROM_24LC32A

CHAR_WIDTH = 6

TFT_WIDTH  = 160 # px
TFT_HEIGHT = 128 # px

btn_up      = Pin(3, Pin.IN, Pin.PULL_UP)
btn_down    = Pin(5, Pin.IN, Pin.PULL_UP)
btn_left    = Pin(2, Pin.IN, Pin.PULL_UP)
btn_right   = Pin(6, Pin.IN, Pin.PULL_UP)
btn_select  = Pin(4, Pin.IN, Pin.PULL_UP)
btn_shift   = Pin(15, Pin.IN, Pin.PULL_UP)

# TFT init
WHITE = const(0XFFFFFF)
tft_spi = SPI(1, baudrate=10000000, sck=Pin(10), mosi=Pin(11))
dc = 7; reset = 8; cs = 9;
tft = TFT(tft_spi, dc, reset, cs)
tft.rotation(3)
tft.initr()
tft.rgb(True)
tft.fill(TFT.BLACK)
tft.text(( 0,  1), "booting...", TFT.WHITE, sysfont, 1)

# EEPROM I2C
#eeprom_i2c = I2C(0, scl=Pin(13), sda=Pin(12))
eeprom = EEPROM_24LC32A(scl=Pin(13), sda=Pin(12), wp=Pin(14, Pin.OUT))

# SD Card init
sd_spi = SPI(0, baudrate=2000000,
             polarity=0, phase=0, bits=8,
             sck=Pin(18), mosi=Pin(19), miso=Pin(16))
try:
    sd = SDCard(sd_spi, cs=Pin(17))
except OSError:
    # TODO: no SD card found
    tft.fill(TFT.BLACK)
    tft.text(( 0,  1), "no SD card found...\ncheck the card.", TFT.WHITE, sysfont, 2)
    raise

SPN_ROOT_DIR = "/sd"

vfs  = uos.VfsFat(sd)
os.mount(sd, SPN_ROOT_DIR)

global TXT_SIZE, Y_START

TXT_SIZE = 1
Y_START = 2

fv_files = [f for f in os.listdir(SPN_ROOT_DIR) if f.endswith(".spn")]

cursor_pos = 0
MAX_FILE_ON_DISP = 9
file_list_offs = [0, MAX_FILE_ON_DISP]

slot_pos = 0
fv_program_slots = {
        0: "",
        1: "",
        2: "",
        3: "",
        4: "",
        5: "",
        6: "",
        7: "",
        }

def draw_file_list():
    Y_START = 1
    for y_offs, name in enumerate(fv_files[ file_list_offs[0] : file_list_offs[1]+1 ]):
        color = TFT.WHITE
        if name in fv_program_slots.values():
            # TODO: show the slot
            inv_map = {v: k for k, v in fv_program_slots.items()}
            tft.text(( 1,  Y_START ), str(inv_map[name]+1), color, sysfont, TXT_SIZE, nowrap=True)
            pass
        if y_offs + file_list_offs[0] == cursor_pos:
            # highlight selected file
            color = TFT.GREEN
        tft.text(( 15,  Y_START ), name, color, sysfont, TXT_SIZE, nowrap=True)
        Y_START += 4+TXT_SIZE*8


############################
# MAIN
############################

# TODO: make a menu

tft.fill(TFT.BLACK)
draw_file_list()

print(file_list_offs)

# TODO: main loop
last_ticks_btn = 0
last_ticks_slot_blink = 0

is_slot_selection = False
sel_blink = False
slot_to_change = 0
while(1):
    #####################
    # SCROLL FILES
    #####################
    scroll_mul = 1
    if not is_slot_selection and time.ticks_ms() - last_ticks_btn > 250 and btn_down.value() == 0:
        tft.fill(TFT.BLACK)
        # scroll down
        if btn_shift.value() == 0:
            scroll_mul = MAX_FILE_ON_DISP

        cursor_pos += 1 * scroll_mul

        if cursor_pos > file_list_offs[1]:
            file_list_offs[0] = file_list_offs[0] + 1 * scroll_mul
            file_list_offs[1] = file_list_offs[1] + 1 * scroll_mul

        if file_list_offs[1] > len(fv_files)-1:
            # roll over to beginning
            file_list_offs[0] = 0
            file_list_offs[1] = MAX_FILE_ON_DISP
            cursor_pos = 0

        if cursor_pos > len(fv_files)-1:
            cursor_pos = 0

        # redraw screen
        draw_file_list()
        # update btn debounce
        last_ticks_btn = time.ticks_ms()
        print(f"scroll down: cursor_pos {cursor_pos} | f: {fv_files[cursor_pos]}")

    if not is_slot_selection and time.ticks_ms() - last_ticks_btn > 250 and btn_up.value() == 0:
        tft.fill(TFT.BLACK)
        # scroll up
        if btn_shift.value() == 0:
            scroll_mul = MAX_FILE_ON_DISP

        cursor_pos = cursor_pos - 1 * scroll_mul

        if cursor_pos < file_list_offs[0]:
            file_list_offs[0] = file_list_offs[0] - 1 * scroll_mul
            file_list_offs[1] = file_list_offs[1] - 1 * scroll_mul

        if file_list_offs[0] < 0:
            # roll over
            file_list_offs[0] = len(fv_files)-1 - MAX_FILE_ON_DISP
            file_list_offs[1] = len(fv_files)-1
            cursor_pos = len(fv_files)-1

        if cursor_pos < 0:
            cursor_pos = len(fv_files)-1

        draw_file_list()
        # update btn debounce
        last_ticks_btn = time.ticks_ms()
        print(f"scroll up: cursor_pos {cursor_pos} | f: {fv_files[cursor_pos]}")

    #####################
    # SLOT SELECTION
    #####################

    if is_slot_selection and time.ticks_ms() - last_ticks_btn > 250 and btn_select.value() == 0:
        # select program for slot
        if not slot_pos == -1:
            # check for duplicates
            if fv_files[cursor_pos] in fv_program_slots.values():
                print("program in use")
                # delete occurence
                for k in fv_program_slots.keys():
                    if fv_program_slots[k] == fv_files[cursor_pos]:
                        fv_program_slots[k] = ""
            fv_program_slots[slot_pos] = fv_files[cursor_pos]
            print(f"slot {slot_pos}: {fv_files[cursor_pos]}")
        if slot_pos == -1 and fv_files[cursor_pos] in fv_program_slots.values():
            # delete slot
            print(f"delete slot")
            for k in fv_program_slots.keys():
                if fv_program_slots[k] == fv_files[cursor_pos]:
                    fv_program_slots[k] = ""
        print(fv_program_slots)
        is_slot_selection = False
        print("stop slot selection")
        tft.fill(TFT.BLACK)
        draw_file_list()
        last_ticks_btn = time.ticks_ms()

    if is_slot_selection and time.ticks_ms() - last_ticks_slot_blink > 200:
        pos = (2, Y_START+(cursor_pos-file_list_offs[0])*TXT_SIZE*11+4)
        # blink slot selection num
        if sel_blink and slot_pos >= 0:
            color = TFT.GREEN
            if fv_program_slots[slot_pos] != "":
                color = TFT.YELLOW
            tft.text(pos, f"{slot_pos+1}", color, sysfont, TXT_SIZE)
        elif sel_blink and slot_pos == -1:
            tft.text(pos, "-", TFT.WHITE, sysfont, TXT_SIZE)
        else:
            tft.fillrect(pos, (10,10), TFT.BLACK)
        sel_blink = not sel_blink
        last_ticks_slot_blink = time.ticks_ms()

    # change slot of program
    if time.ticks_ms() - last_ticks_btn > 250 and btn_left.value() == 0:
        if not is_slot_selection:
            is_slot_selection = True
        else:
            slot_pos = slot_pos-1
        if slot_pos < -1:
            slot_pos = 7
        last_ticks_btn = time.ticks_ms()

    if time.ticks_ms() - last_ticks_btn > 250 and btn_right.value() == 0:
        if not is_slot_selection:
            is_slot_selection = True
        else:
            slot_pos = slot_pos+1
        if slot_pos > 7:
            slot_pos = -1
        last_ticks_btn = time.ticks_ms()

    #####################
    # PROGRAM EEPROM
    #####################
    if not is_slot_selection and time.ticks_ms() - last_ticks_btn > 250 and btn_select.value() == 0:
        # program eeproms as blocking call
        tft.fill(TFT.BLACK)
        has_eeprom = True
        if len(eeprom.i2c.scan()) == 0:
            has_eeprom = False
        if not len([i for i in fv_program_slots.values() if i ==""]) >= 8 and has_eeprom:
            print("start programming")
            eeprom_addr = eeprom.i2c.scan()[0]
            # something in dict
            for slot in range(8):
                txt_pos = (1, 2+slot*10)
                if fv_program_slots[slot] == "":
                    tft.text(txt_pos, f"slot{slot+1} empty", TFT.WHITE, sysfont, 1)
                    continue
                print(f"slot {slot}: {fv_program_slots[slot]}")
                spn_content = b""
                gc.collect() # free some RAM for this!
                with open(f"{SPN_ROOT_DIR}/{fv_program_slots[slot]}", "rb") as f:
                    try:
                        for line in f.readlines():
                            if line.startswith(b";") \
                                or line.startswith(b"\r") \
                                or line.startswith(b"\n"):
                                continue
                            spn_content += line.split(b";")[0]
                    except MemoryError:
                        # TODO: wat to do with Error
                        print("MemoryError: file content too big for RAM")
                        tft.text(txt_pos, f"slot{slot+1} ERROR:file too big!", TFT.RED, sysfont, 1)
                        continue

                encoding = 'utf-8'
                # check for BOM
                if len(spn_content) > 2 and spn_content[0] == 0xFF and spn_content[1] == 0xFE:
                    encoding = 'utf-16le'
                elif len(spn_content) > 2 and spn_content[0] == 0xFE and spn_content[1] == 0xFF:
                    encoding = 'utf-16be'
                # or assume windows encoded 'ANSI'
                elif len(spn_content) > 7 and spn_content[7] == 0x00:
                    encoding = 'utf-16le'

                fv1_parser = asfv1.fv1parse(spn_content.decode(encoding, 'replace'),
                                            clamp=True, spinreals=True,
                                            wfunc=asfv1.warning, efunc=asfv1.error
                                           )
                for attempt in range(3):
                    try:
                        fv1_parser.parse()
                    except asfv1.ASFV1Error:
                        if attempt == 0:
                            fv1_parser.doclamp = False
                            fv1_parser.spinreals = True
                        elif attempt == 1:
                            fv1_parser.doclamp = True
                            fv1_parser.spinreals = False
                        elif attempt == 2:
                            fv1_parser.doclamp = False
                            fv1_parser.spinreals = False
                        print("assembler error. trying again")
                        continue
                    else:
                        # reset to startign flags
                        print("did work now")
                        fv1_parser.doclamp = True
                        fv1_parser.spinreals = True
                        break
                else:
                    # TODO: program does not assemble
                    tft.text(txt_pos, f"slot{slot+1} ERROR:file not valid!", TFT.RED, sysfont, 1)
                    continue

                # write to EEPROM
                mem_offs = 0x200 * slot
                eeprom.write_data(mem_offs, fv1_parser.program)
                if fv1_parser.program == eeprom.read_data(mem_offs, 0x200):
                    print("program check OK!")
                    tft.text(txt_pos, f"slot{slot+1} okay!", TFT.WHITE, sysfont, 1)
                else:
                    tft.text(txt_pos, f"slot{slot+1} ERROR:not written!", TFT.RED, sysfont, 1)

                # free RAM so it does not fill while assembling
                del spn_content
                del fv1_parser
                gc.collect() # free some RAM for this!

            tft.text((10, txt_pos[1]+22), f"press select button", TFT.YELLOW, sysfont, 1)
            tft.text((10, txt_pos[1]+34), f"to continue", TFT.YELLOW, sysfont, 1)
            while btn_select.value():
                pass
        elif len([i for i in fv_program_slots.values() if i ==""]) >= 8:
            print("no files selected")
            # dict empty
            tft.text((2, 10), "No", TFT.RED, sysfont, 3)
            tft.text((2, 40), "programs", TFT.RED, sysfont, 3)
            tft.text((2, 70), "selected", TFT.RED, sysfont, 3)
            time.sleep(3)
        elif not has_eeprom:
            print("no eeprom found")
            tft.text((2, 10), "No", TFT.RED, sysfont, 3)
            tft.text((2, 40), "EEPROM", TFT.RED, sysfont, 3)
            tft.text((2, 70), "found", TFT.RED, sysfont, 3)
            time.sleep(3)

        # reset to selection screen
        tft.fill(TFT.BLACK)
        draw_file_list()
        last_ticks_btn = time.ticks_ms()
