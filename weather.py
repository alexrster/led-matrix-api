import requests
import datetime

class OpenWeatherMap(object):
  def __init__(self, appid):
    self.params = {
        'appid': appid,
        'q': 'Kiev',
        'units': 'metric'
    }
    self.led_brightness = 100
    self.day_phase = 'day'
    self.update()
  
  def update(self):
    api_result = requests.get('https://api.openweathermap.org/data/2.5/weather', self.params)
    api_response = api_result.json()

    sunrise = datetime.datetime.fromtimestamp(api_response['sys']['sunrise'])
    sunset = datetime.datetime.fromtimestamp(api_response['sys']['sunset'])
    now = datetime.datetime.now()

    if sunrise - now > datetime.timedelta(minutes=30):
        self.led_brightness = 1
        self.day_phase = 'night'
    elif now - sunset > datetime.timedelta(minutes=30):
        self.led_brightness = 1
        self.day_phase = 'night'
    elif now - sunrise <= datetime.timedelta(minutes=30):
        self.led_brightness = 40
        self.day_phase = 'sunrise'
    elif sunset - now <= datetime.timedelta(minutes=30):
        self.led_brightness = 40
        self.day_phase = 'sunset'
    else:
        self.led_brightness = 100
        self.day_phase = 'day'
    
    self.temp = api_response['main']['temp']

    #print(u'Current temperature in %s is %d℃, sun is coming from %s till %s, current time %s – led brightness: %d, because of %s now!' % (api_response['name'], api_response['main']['temp'], sunrise, sunset, now, led_brightness, day_phase))
