import requests
import datetime

SUNRISE_THRESHOLD_MIN=90
SUNSET_THRESHOLD_MIN=90
LIGHT_INTENSITY_MAX=80
QUERY_FREQUENCY_MIN=60

class OpenWeatherMap(object):
  def __init__(self, appid):
    self.params = {
        'appid': appid,
        'q': 'Kiev',
        'units': 'metric'
    }
    self.lightIntensity = LIGHT_INTENSITY_MAX
    self.dayPhase = 'day'
    self.lastDataTimestamp = None
    self.lastData = None

    self.update()
  
  def update(self):
    now = datetime.datetime.now()

    # Don't query web service too often (free subscription is always limited by number of calls per month)
    if self.lastData is None or self.lastDataTimestamp is None or now - self.lastDataTimestamp > datetime.timedelta(minutes=QUERY_FREQUENCY_MIN):
        self.lastData = requests.get('https://api.openweathermap.org/data/2.5/weather', self.params).json()
        self.lastDataTimestamp = now

        self.sunrise = datetime.datetime.fromtimestamp(self.lastData['sys']['sunrise'])
        self.sunset = datetime.datetime.fromtimestamp(self.lastData['sys']['sunset'])    
        self.temp = self.lastData['main']['temp']

    if self.sunrise - now > datetime.timedelta(minutes=SUNRISE_THRESHOLD_MIN) or now - self.sunset > datetime.timedelta(minutes=SUNSET_THRESHOLD_MIN):
        self.lightIntensity = 1
        self.dayPhase = 'night'
        self.nextDayPhase = 'sunrise'
        self.nextDayPhaseStart = self.sunrise
    elif now - self.sunrise <= datetime.timedelta(minutes=SUNRISE_THRESHOLD_MIN):
        self.lightIntensity = self.lightIntensity / SUNRISE_THRESHOLD_MIN * ((now - self.sunrise).seconds / 60)
        self.dayPhase = 'sunrise'
        self.nextDayPhase = 'day'
        self.nextDayPhaseStart = self.sunrise + datetime.timedelta(minutes=SUNRISE_THRESHOLD_MIN)
    elif now - self.sunset <= datetime.timedelta(minutes=SUNSET_THRESHOLD_MIN):
        self.lightIntensity = self.lightIntensity / SUNSET_THRESHOLD_MIN * ((datetime.timedelta(minutes=SUNSET_THRESHOLD_MIN) - (now - self.sunset)).seconds / 60)
        self.dayPhase = 'sunset'
        self.nextDayPhase = 'night'
        self.nextDayPhaseStart = self.sunset + datetime.timedelta(minutes=SUNSET_THRESHOLD_MIN)
    else:
        self.lightIntensity = LIGHT_INTENSITY_MAX
        self.dayPhase = 'day'
        self.nextDayPhase = 'sunset'
        self.nextDayPhaseStart = self.sunset
