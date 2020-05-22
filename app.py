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
idle = 0

@app.route('/set/')
def set_text():
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
    idle = 0
    msg = request.args.get('msg')
    fontName = parse_font_name(request.args.get('font'))
    font = proportional(fontName) if request.args.get('proportional') else tolerant(fontName)
    
    show_message(device, msg, fill="white", font=font)
    idle = 0
    
    return msg

def parse_font_name(font_name):
    return fonts.get(font_name, SINCLAIR_FONT)

@tl.job(interval=timedelta(seconds=1))
def timer_1s():
    idle += 1
    logger.info("1s timer tick, idle counter = " + idle)
    if idle <= IDLE_MIN:
        return

    logger.info("Attempt to draw")
    str_template = "%H:%M" if idle % 2 > 0 else "%H %M"
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline=black, fill=white)
        text(draw, (0, 0), time.strftime(str_template, time.ctime()), fillColor=white, font=proportional(LCD_FONT)) 

#if __name__ == '__main__':
#logger.info('Starting app')
#app.run()
    
logger.info('Starting timeloop')
tl.start(block=False)

logger.info('Starting app')
