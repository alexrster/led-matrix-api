import requests
import datetime

DATA_REFRESH_MINS=60
SUNRISE_THRESHOLD_MINS=40
SUNSET_THRESHOLD_MINS=40
LIGHT_INTENSITY_MAX=100
LIGHT_INTENSITY_MIN=1

class OpenWeatherMap(object):
  def __init__(self, appid):
    self.params = {
        'appid': appid,
        'q': 'Kiev',
        'units': 'metric'
    }
    self.lightIntensity = LIGHT_INTENSITY_MIN
    self.dayPhase = 'night'
    self.lastDataTimestamp = None
    self.lastData = None

    self.update()
  
  def update(self):
    now = datetime.datetime.now()

    # Don't query web service too often (free subscription is always limited by number of calls per month)
    if self.lastData is None or self.lastDataTimestamp is None or now - self.lastDataTimestamp > datetime.timedelta(minutes=DATA_REFRESH_MINS):
        self.lastData = requests.get('https://api.openweathermap.org/data/2.5/weather', self.params).json()
        self.lastDataTimestamp = now

        self.sunrise = datetime.datetime.fromtimestamp(self.lastData['sys']['sunrise'])
        self.sunset = datetime.datetime.fromtimestamp(self.lastData['sys']['sunset'])    
        self.temp = self.lastData['main']['temp']

    if self.sunrise - now > datetime.timedelta(minutes=SUNRISE_THRESHOLD_MINS) or now - self.sunset > datetime.timedelta(minutes=SUNSET_THRESHOLD_MINS):
        self.lightIntensity = LIGHT_INTENSITY_MIN
        self.dayPhase = 'night'
        self.nextDayPhase = 'sunrise'
        self.nextDayPhaseStart = self.sunrise
    elif now - self.sunrise <= datetime.timedelta(minutes=SUNRISE_THRESHOLD_MINS):
        light = ((now - self.sunrise).seconds / 60) * LIGHT_INTENSITY_MAX / SUNRISE_THRESHOLD_MINS
        self.lightIntensity = light if light > LIGHT_INTENSITY_MIN else LIGHT_INTENSITY_MIN
        self.dayPhase = 'sunrise'
        self.nextDayPhase = 'day'
        self.nextDayPhaseStart = self.sunrise + datetime.timedelta(minutes=SUNRISE_THRESHOLD_MINS)
    elif now - self.sunset <= datetime.timedelta(minutes=SUNSET_THRESHOLD_MINS):
        light = ((datetime.timedelta(minutes=SUNSET_THRESHOLD_MINS) - (now - self.sunset)).seconds / 60) * LIGHT_INTENSITY_MAX / SUNSET_THRESHOLD_MINS
        self.lightIntensity = light if light > LIGHT_INTENSITY_MIN else LIGHT_INTENSITY_MIN
        self.dayPhase = 'sunset'
        self.nextDayPhase = 'night'
        self.nextDayPhaseStart = self.sunset + datetime.timedelta(minutes=SUNSET_THRESHOLD_MINS)
    else:
        self.lightIntensity = LIGHT_INTENSITY_MAX
        self.dayPhase = 'day'
        self.nextDayPhase = 'sunset'
        self.nextDayPhaseStart = self.sunset
