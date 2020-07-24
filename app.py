import time
import logging
import sys
import signal
import pybrake

from flask import Flask, request
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport, hotspot, snapshot
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

notifier = pybrake.Notifier(project_id=275208,
                            project_key='01406c349e7152afb3c85714bf64cafe',
                            environment='production')

app = Flask(__name__)
tl = Timeloop()

fonts = {
    'cp437': CP437_FONT,
    'tiny': TINY_FONT,
    'sinclair': SINCLAIR_FONT,
    'lcd': LCD_FONT
}

class textSnapshot(snapshot):
    def __init__(self, text, font, color="white"):
        self.text = text
        self.font = font
        self.color = color
        self.width = 32
        self.height = 8
        txtlen, _ = textsize(self.text, font=self.font)
        self.coords = (self.width - txtlen + 1, 0)
        snapshot.__init__(self, self.width, self.height, interval=3600.0)
    
    def update(self, draw):
        text(draw, self.coords, self.text, fill=self.color, font=self.font)

class blinkingTextSnapshot(snapshot):
    def __init__(self, text, font, duration=1):
        self.text = text
        self.font = font
        self.color = "white"
        self.backColor = "black"
        self.size = textsize(text, font)
        self.width, self.height = self.size
        snapshot.__init__(self, self.width, self.height, self.update, duration)
    
    def update(self, draw):
        self.color = "black" if self.backColor=="black" else "white"
        self.backColor = "white" if self.backColor=="black" else "black"
        draw.rectangle((0, 0, self.width, self.height), outline=self.backColor, fill=self.backColor)
        text(draw, (1, 0), self.text, fill=self.color, font=self.font)

class currentDateSnapshot(snapshot):
    def __init__(self):
        self.currentView = 0
        self.forceRedraw = False
        snapshot.__init__(self, 35, 8, self.update, 15.0)
    
    def update(self, draw):
        self.currentView  = 1 if self.currentView == 0 else 0
        date_str = time.strftime("%d %B") if self.currentView == 1 else time.strftime("%A")
        txtlen, _ = textsize(date_str, font=utils.proportional2(TINY_FONT))
        coords = (36 - txtlen, 2)
        text(draw, coords, date_str, fill="white", font=utils.proportional2(TINY_FONT))

    def invalidate(self):
        self.forceRedraw = True

    def should_redraw(self):
        if self.forceRedraw:
            self.forceRedraw = False
            return True
        else:
            return snapshot.should_redraw(self)

def deviceInit(s):
    return max7219(s, cascaded=8, block_orientation=90, rotate=0, blocks_arranged_in_reverse_order=1)

serial = spi(port=0, device=0, gpio=noop())
device = deviceInit(serial)
deviceViewport = viewport(device, 64, 8)

@app.route('/marquee/')
@app.route('/set/')
def set_text():
    global deviceViewport

    text = request.args.get('msg')
    fontName = parse_font_name(request.args.get('font'))
    font = proportional(fontName) if request.args.get('proportional') else tolerant(fontName)
    set_contentHotspot(textSnapshot(text=text, font=font), (32, 0))

    return 'OK'

@app.route('/blink/')
def set_text_blink():
    global deviceViewport

    text = request.args.get('msg')
    fontName = parse_font_name(request.args.get('font'))
    font = proportional(fontName) if request.args.get('proportional') else tolerant(fontName)
    duration = request.args.get('duration', default=600, type=int)
    set_contentHotspot(blinkingTextSnapshot(text=text, font=font, duration=duration/1000), (32, 0))

    return 'OK'

@app.route('/clear/')
def clear():
    global deviceViewport, dateSnapshot
    set_contentHotspot(dateSnapshot, (29, 0))
    dateSnapshot.invalidate()

    return 'OK'

@app.route('/reset/')
def reset():
    global device, serial
    device.cleanup()
    device = deviceInit(serial)
    device.show()

    return 'OK'

# @app.route('/marquee/')
# def marquee_text():
#     return

intensity = 1
is_hidden = False

@app.route('/lightbulb/set/')
def lightbulb_set_brightness():
    global intensity
    return str(set_brightness(request.args.get('brightness', default=intensity, type=int)))

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

def set_brightness(value):
    global intensity
    global is_hidden
    intensity = value
    is_hidden = False if intensity > 0 else True
    device.contrast(int(value * 255 / 100))
    return value

def parse_font_name(font_name):
    return fonts.get(font_name, SINCLAIR_FONT)

def drawClock(draw, width = 0, height = 0):
    time_str = time.strftime("%H:%M" if int(time.time()) % 2 > 0 else "%H %M")
    coords = (0, 1)
    text(draw, coords, time_str, fill="white", font=utils.proportional2(LCD_FONT))

contentHotspot = None
contentHotspotXY = None
def set_contentHotspot(hotspot, xy):
    global deviceViewport, contentHotspot, contentHotspotXY
    if contentHotspot != None:
        deviceViewport.remove_hotspot(contentHotspot, contentHotspotXY)
    deviceViewport.add_hotspot(hotspot, xy)
    contentHotspot = hotspot
    contentHotspotXY = xy

clockSnapshot = snapshot(29, 8, drawClock, 1.0)
dateSnapshot = currentDateSnapshot()

deviceViewport.add_hotspot(clockSnapshot, (0, 0))
set_contentHotspot(dateSnapshot, (29, 0))

deviceViewport.refresh()
set_brightness(intensity)

@tl.job(interval=timedelta(milliseconds=50))
def onDraw():
    global deviceViewport
    deviceViewport.refresh()

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

logger.info('Started!')