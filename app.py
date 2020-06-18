import time
import logging
import sys
import signal

from flask import Flask, request
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message, textsize
from luma.core.legacy.font import proportional, tolerant, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT
from timeloop import Timeloop
from datetime import timedelta

import utils

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

logger.info('Initialize Led Matrix API')

app = Flask(__name__)
tl = Timeloop()

fonts = {
    'cp437': CP437_FONT,
    'tiny': TINY_FONT,
    'sinclair': SINCLAIR_FONT,
    'lcd': LCD_FONT
}

serial = spi(port=0, device=0, gpio=noop())
device = max7219(serial, cascaded=8, block_orientation=90, rotate=0, blocks_arranged_in_reverse_order=1)
IDLE_MIN = 5
idle = IDLE_MIN
intensity = 100
is_hidden = False

@app.route('/set/')
def set_text():
    global idle
    idle = 0
    msg = request.args.get('msg')
    inv = request.args.get('invert', default=0, type=int)
    fillColor = "black" if inv > 0 else "white"
    backColor = "white" if inv > 0 else "black"
    fontName = parse_font_name(request.args.get('font'))
    font = proportional(fontName) if request.args.get('proportional') else tolerant(fontName)
    x = request.args.get('x', default=33, type=int)
    y = request.args.get('y', default=0, type=int)

    target_rect = (32, 0, 64, 8)
    #target_rect = device.bounding_box

    with canvas(device) as draw:
        draw.rectangle(target_rect, outline=backColor, fill=backColor)
        text(draw, (x, y), msg, fill=fillColor, font=font)

    return msg

@app.route('/marquee/')
def marquee_text():
    global idle
    idle = -1000000
    msg = request.args.get('msg')
    fontName = parse_font_name(request.args.get('font'))
    font = proportional(fontName) if request.args.get('proportional') else proportional(fontName)
    
    show_message(device, msg, fill="white", font=font)
    idle = IDLE_MIN-1
    timer_1s()
    
    return msg

@app.route('/lightbulb/set/')
def lightbulb_set_brightness():
    return str(set_brightness(request.args.get('brightness', default=100, type=int)))

@app.route('/lightbulb/brightness/')
def lightbulb_get_brightness():
    global intensity
    global is_hidden    
    return str(0 if is_hidden else intensity)

@app.route('/lightbulb/status/')
def lightbulb_get_status():
    global is_hidden
    return "0" if is_hidden else "1"

@app.route('/lightbulb/on/')
def lightbulb_set_on():
    global is_hidden
    global intensity
    is_hidden = False
    device.show()
    return str(intensity)

@app.route('/lightbulb/off/')
def lightbulb_set_off():
    global is_hidden
    is_hidden = True
    device.hide()
    return "0"

def update_clock():
    time_str = time.strftime("%H:%M" if idle % 2 > 0 else "%H %M")
    #(txtlen, _) = textsize(time_str, font=utils.proportional2(SINCLAIR_FONT))
    #coords = (int((32-txtlen)/2), 0)
    coords = (1, 0)
    with canvas(device) as draw:
        text(draw, coords, time_str, fill="white", font=utils.proportional2(SINCLAIR_FONT))
#        text(draw, (48, 0), chr(0x0F), fill="white", font=CP437_FONT)

def set_brightness(value):
    global intensity
    global is_hidden
    intensity = value
    is_hidden = False if intensity > 0 else True
    device.contrast(int(value * 255 / 100))
    return value

def parse_font_name(font_name):
    return fonts.get(font_name, SINCLAIR_FONT)

@tl.job(interval=timedelta(seconds=1))
def timer_1s():
    global idle
    idle += 1
    if idle < IDLE_MIN:
        return

    update_clock()
    
logger.info('Starting timeloop')
tl.start(block=False)

logger.info('Subscribe to OS signals')
def app_quit(signal, frame):
    print("Got signal {}".format(signal))
    print("Stop timeloop")
    tl.stop()

    print("Stop device")
    device.cleanup()

    print("Exiting app")
    sys.exit(0)

signal.signal(signal.SIGTERM, app_quit)
signal.signal(signal.SIGINT, app_quit)

logger.info('')