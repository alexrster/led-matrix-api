import requests
import datetime
import math

DATA_REFRESH_MINS=60
SUNRISE_THRESHOLD_MINS=40
SUNSET_THRESHOLD_MINS=40
SUNLIGHT_INTENSITY_MAX=100
SUNLIGHT_INTENSITY_MIN=1

class SunLight(object):
    def __init__(self, sunrise, sunset):
        #self.date = sunrise.date.date()
        self.sunrise = sunrise
        self.sunset = sunset
        self._dayDuration = (sunset - sunrise).seconds
        self._noonPoint = int(self._dayDuration / 2)
        self._a2 = self._noonPoint * self._noonPoint
    
    def getIntensity(self, time):
        if time <= self.sunrise or time >= self.sunset:
            return 0

        dayTime = (time - self.sunrise).seconds
        x = dayTime - self._noonPoint
        y = math.sqrt(1 - x * x / self._a2)
        return y

class OpenWeatherMap(object):
  def __init__(self, appid):
    self.params = {
        'appid': appid,
        'q': 'Kiev',
        'units': 'metric'
    }
    self.lightIntensity = SUNLIGHT_INTENSITY_MIN
    self.dayPhase = 'night'
    self.lastDataTimestamp = datetime.datetime.min
    self.lastData = None
    self._sunLight = None

    self.update()
  
  def update(self):
    now = datetime.datetime.now()

    # Don't query web service too often (free subscription is always limited by number of calls per month)
    if self.lastData is None or self.lastDataTimestamp + datetime.timedelta(minutes=DATA_REFRESH_MINS) <= now:
        self.lastData = requests.get('https://api.openweathermap.org/data/2.5/weather', self.params).json()
        self.lastDataTimestamp = now

        self.sunrise = datetime.datetime.fromtimestamp(self.lastData['sys']['sunrise'])
        self.sunset = datetime.datetime.fromtimestamp(self.lastData['sys']['sunset'])    
        self.temp = self.lastData['main']['temp']

        if self._sunLight is None or self._sunLight.sunrise != self.sunrise:
            self._sunLight = SunLight(self.sunrise, self.sunset)

    light = int(self._sunLight.getIntensity(now) * SUNLIGHT_INTENSITY_MAX)
    self.lightIntensity = light if light > SUNLIGHT_INTENSITY_MIN else SUNLIGHT_INTENSITY_MIN
