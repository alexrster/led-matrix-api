from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message, textsize
from luma.core.legacy.font import proportional, tolerant, CP437_FONT, TINY_FONT, SINCLAIR_FONT, LCD_FONT

class sprite(object):
  def render(self, draw):
    """
    Draw current sprite frame. The function intended to be triggered each 50ms.

    :param draw: :luma.core.canvas
    """
    raise NotImplementedError

class textSprite(sprite):
  def __init__(self, text, coords = (0, 0), blinkingRate = 667, timeout = 0):
    self.blinkingRate = blinkingRate
    self.timeout = timeout

  def render(self, draw):
    pass

class blinkingTextSprite(sprite):
  def __init__(self, coords = (0, 0), blinkingRate = 667, timeout = 0):
    self.blinkingRate = blinkingRate
    self.timeout = timeout

  def render(self, draw):
    pass