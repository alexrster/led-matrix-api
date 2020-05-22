import time
import logging
import sys

from flask import Flask, request
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message
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
device = max7219(serial, cascaded=4, block_orientation=90, rotate=0, blocks_arranged_in_reverse_order=1)
IDLE_MIN = 5
idle = IDLE_MIN
intensity = 100

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
    x = request.args.get('x', default=1, type=int)
    y = request.args.get('y', default=0, type=int)

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline=backColor, fill=backColor)
        text(draw, (x, y), msg, fill=fillColor, font=font)
    idle = 0

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
    return str(intensity)

@app.route('/lightbulb/status/')
def lightbulb_get_status():
    return str('1' if intensity > 0 else '0')

@app.route('/lightbulb/on/')
def lightbulb_set_on():
    return str(set_brightness(100))

@app.route('/lightbulb/off/')
def lightbulb_set_off():
    return str(set_brightness(0))

def set_brightness(value):
    global intensity
    intensity = value
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

    str = time.strftime("%H:%M" if idle % 2 > 0 else "%H %M")
    with canvas(device) as draw:
        text(draw, (0, 0), str, fill="white", font=utils.proportional2(SINCLAIR_FONT)) 
    
logger.info('Starting timeloop')
tl.start(block=False)

logger.info('Starting app')
