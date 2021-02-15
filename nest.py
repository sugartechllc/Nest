import requests
import sys
import json
import time
import datetime
from datetime import datetime, timezone

CONFIG = {}
FILE_NAME = ''
VERBOSE = False

def generate_login_url():
  url = 'https://nestservices.google.com/partnerconnections/'+ \
    CONFIG['nest']['project_id']+'/auth?redirect_uri='+ \
    CONFIG['nest']['redirect_uri']+ \
    '&access_type=offline&prompt=consent&client_id='+ \
    CONFIG['nest']['client_id']+ \
    '&response_type=code&scope=https://www.googleapis.com/auth/sdm.service'
  return(url)

def get_tokens():
  # Get access and refresh tokens
  params = (
    ('client_id', CONFIG['nest']['client_id']),
    ('client_secret', CONFIG['nest']['client_secret']),
    ('code', CONFIG['nest']['code']),
    ('grant_type', 'authorization_code'),
    ('redirect_uri', CONFIG['nest']['redirect_uri']),
  )
  response = requests.post('https://www.googleapis.com/oauth2/v4/token', params=params)
  response_json = response.json()
  if VERBOSE:
    print(response_json)
  access_token = response_json['token_type'] + ' ' + str(response_json['access_token'])
  if VERBOSE:
    print('Access token: ' + access_token)
  refresh_token = response_json['refresh_token']
  if VERBOSE:
    print('Refresh token: ' + refresh_token)
  CONFIG['nest']['access_token'] = access_token
  CONFIG['nest']['refresh_token'] = refresh_token
  write_config()
  return

def refresh_token():
  # Refresh token
  params = (
      ('client_id', CONFIG['nest']['client_id']),
      ('client_secret', CONFIG['nest']['client_secret']),
      ('refresh_token', CONFIG['nest']['refresh_token']),
      ('grant_type', 'refresh_token'),
  )
  response = requests.post('https://www.googleapis.com/oauth2/v4/token', params=params)
  response_json = response.json()
  access_token = response_json['token_type'] + ' ' + response_json['access_token']
  if VERBOSE:
    print('Access token: ' + access_token)
  CONFIG['nest']['access_token'] = access_token
  write_config()

def get_structures():
  # Get structures
  url_structures = 'https://smartdevicemanagement.googleapis.com/v1/enterprises/' + CONFIG['nest']['project_id'] + '/structures'
  headers = {
      'Content-Type': 'application/json',
      'Authorization': CONFIG['nest']['access_token'],
  }
  response = requests.get(url_structures, headers=headers)
  if VERBOSE:
    print(json.dumps(response.json(), indent = 2, separators=(',', ': ')))

def get_devices():
  # Get devices
  url_get_devices = 'https://smartdevicemanagement.googleapis.com/v1/enterprises/' + CONFIG['nest']['project_id'] + '/devices'
  headers = {
      'Content-Type': 'application/json',
      'Authorization': CONFIG['nest']['access_token'],
  }
  response = requests.get(url_get_devices, headers=headers)
  if VERBOSE:
    print(json.dumps(response.json(), indent = 2, separators=(',', ': ')))
  response_json = response.json()
  device_0_name = response_json['devices'][0]['name']
  if VERBOSE:
    print(device_0_name)
  return device_0_name

def get_device_stats(device_name):
  time_stamp = datetime.now(timezone.utc).isoformat()
  # Get device stats
  url_get_device = 'https://smartdevicemanagement.googleapis.com/v1/' + device_name
  headers = {
      'Content-Type': 'application/json',
      'Authorization': CONFIG['nest']['access_token'],
  }
  response = requests.get(url_get_device, headers=headers)
  if VERBOSE:
    print(json.dumps(response.json(), indent = 2, separators=(',', ': ')))
  response_json = response.json()
  retval = {}
  retval['time'] = time_stamp
  retval['status'] = response_json['traits']['sdm.devices.traits.ThermostatHvac']['status']
  retval['mode'] = response_json['traits']['sdm.devices.traits.ThermostatMode']['mode']
  retval['tempC'] = response_json['traits']['sdm.devices.traits.Temperature']['ambientTemperatureCelsius']
  retval['tempF'] = retval['tempC']*9.0/5.0 + 32.0
  retval['RH']  = response_json['traits']['sdm.devices.traits.Humidity']['ambientHumidityPercent']
  retval['ecomode'] = response_json['traits']['sdm.devices.traits.ThermostatEco']['mode']
  #retval['setpointC'] = response_json['traits']['sdm.devices.traits.ThermostatTemperatureSetpoint']['heatCelsius']

  return retval

def get_config():
  global CONFIG
  json_config = open(FILE_NAME).read()
  CONFIG = json.loads(json_config)

def write_config():
  global CONFIG
  f = open(FILE_NAME, 'w')
  f.write(json.dumps(CONFIG, indent = 2, separators=(',', ': ')))

def mod_sleep(interval_secs):
  ''' Sleep until the next even time in seconds. '''
  now = time.time()
  sleep_time = interval_secs - (now+interval_secs) % interval_secs - 0.002
  time.sleep(sleep_time)


def print_config():
  print(json.dumps(CONFIG, indent = 2, separators=(',', ': ')))
  print()

if __name__ == '__main__':
  FILE_NAME = sys.argv[1]
  get_config()
  print_config()

  ans = input('Do you need to create new access and refresh tokens? [y/n] ')
  if ans == 'y' or ans == 'Y':
    login_url = generate_login_url()
    print('A login URL will be generated, that can be used to get a new code, for getting a new access code.')
    print('To ger the code, browse through all of the screens until you get to your redirect_url.')
    print('Google added a query to end that looks like this: ...?code=4/.....&scope=...')
    print('Copy the part between code= and &scope= and add it to the code section in nest.json')
    print("Go to this URL to log in:")
    print(login_url)
    print()
    input('Hit return after you have added the new code into ' + FILE_NAME)
    get_config()
    get_tokens()
    print('The new configuration:')
    print_config()

  refresh_token()
  if VERBOSE:
    print('The refreshed tokens')
    print_config()

  get_structures()

  device_name = get_devices()

  count = 0
  first = True
  while (1):
    if not first:
      mod_sleep(CONFIG['nest']['report_interval'])
    print(get_device_stats(device_name))
    first = False
    count = count + 1
    if count > 55:
      refresh_token()
      count = 0
