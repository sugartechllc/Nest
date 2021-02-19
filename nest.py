import requests
import sys
import json
import time
import datetime
import argparse
from datetime import datetime, timezone
import pychords.tochords as tochords

# TYhe configuration is global!
CONFIG = {}

VERBOSE = False
TEST=False

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
  time_stamp = datetime.now(timezone.utc).isoformat()[:-10]+'Z'
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
  retval['RH']  = response_json['traits']['sdm.devices.traits.Humidity']['ambientHumidityPercent']
  retval['mode'] = response_json['traits']['sdm.devices.traits.ThermostatMode']['mode']
  retval['ecomode'] = response_json['traits']['sdm.devices.traits.ThermostatEco']['mode']
  retval['status'] = response_json['traits']['sdm.devices.traits.ThermostatHvac']['status']
  setpointC = response_json['traits']['sdm.devices.traits.ThermostatTemperatureSetpoint'].get('heatCelsius')
  if setpointC:
    retval['setpointC'] = setpointC
  retval['tempC'] = response_json['traits']['sdm.devices.traits.Temperature']['ambientTemperatureCelsius']

  return retval

def status_translate():
  '''
    "sdm.devices.traits.Info": {
      "customName": ""
    },

    "sdm.devices.traits.Humidity": {
      "ambientHumidityPercent": 30
    },
    *** rh: ambientHumidityPercent

    "sdm.devices.traits.Connectivity": {
      "status": "ONLINE"
    },

    "sdm.devices.traits.Fan": {
      "timerMode": "OFF"
    },

    "sdm.devices.traits.ThermostatMode": {
      "mode": "HEAT",
      "availableModes": [
        "HEAT",
        "COOL",
        "HEATCOOL",
        "OFF"
      ]
    },
    *** mode: HEAT, COOL, HEATCOOL, OFF

    "sdm.devices.traits.ThermostatEco": {
      "availableModes": [
        "OFF",
        "MANUAL_ECO"
      ],
      "mode": "OFF",
      "heatCelsius": 4.5,
      "coolCelsius": 24.444443
    },
    *** ecomode: OFF, MANUAL_ECO

    "sdm.devices.traits.ThermostatHvac": {
      "status": "HEATING"
    },
    *** status: OFF, HEATING, COOLING

    "sdm.devices.traits.Settings": {
      "temperatureScale": "FAHRENHEIT"
    },

    "sdm.devices.traits.ThermostatTemperatureSetpoint": {
      "heatCelsius": 10.121735
    },
    *** setpointC: heatCelsius

    "sdm.devices.traits.Temperature": {
      "ambientTemperatureCelsius": 4.719986
    }
    *** tempC: ambientTemperatureCelsius
  },
  '''
  pass

def get_config(config_file_name):
  global CONFIG
  json_config = open(config_file_name).read()
  CONFIG = json.loads(json_config)

def write_config(config_file_name):
  global CONFIG
  f = open(config_file_name, 'w')
  f.write(json.dumps(CONFIG, indent = 2, separators=(',', ': ')))

def mod_sleep(interval_secs):
  '''
  Sleep until the next even time in seconds. 
  Except on the first call.
  '''
  if not hasattr(mod_sleep,"first_call"):
    mod_sleep.first_call = True

  if mod_sleep.first_call:
    mod_sleep.first_call = False
    return

  now = time.time()
  sleep_time = interval_secs - (now+interval_secs) % interval_secs - 0.002
  time.sleep(sleep_time)

def arg_parse():
  global VERBOSE
  global TEST

  parser = argparse.ArgumentParser(description='Nest to CHORDS.')

  parser.add_argument('config_file', 
                      help='the configuration file')
  parser.add_argument('--interval', action='store',
                      default=None, type=int,
                      help='override the reporting interval (s)')
  parser.add_argument('--new_code', action='store_const',
                      const=True, default=False,
                      help='create URL for obtaining a new access code')
  parser.add_argument('--verbose', action='store_const',
                      const=True, default=False,
                      help='enable verbose output')
  parser.add_argument('--test', action='store_const',
                      const=True, default=False,
                      help='test mode (do not forward data)')
  args = parser.parse_args()

  # Set the globals
  VERBOSE = args.verbose
  TEST = args.test

  if VERBOSE:
    print(args)
    print()

  return args

def print_config():
  print(json.dumps(CONFIG, indent = 2, separators=(',', ': ')))
  print()

def token_renew(config_file_name):
  if not hasattr(token_renew,"last_renew_time"):
      token_renew.last_renew_time=None

  if not token_renew.last_renew_time:
    refresh_token()
    write_config(config_file_name)
    token_renew.last_renew_time = time.time()
    print("tokens renewed")
    return

  # Tokens are good for 60 minutes, so renew close to then
  if time.time() - token_renew.last_renew_time < 55*60:
    return

  refresh_token()
  write_config(config_file_name)
  token_renew.last_renew_time = time.time()
  print("tokens renewed")
  return

def new_code(args):
    login_url = generate_login_url()
    print()
    print('A login URL will be generated, that can be used for getting a new access code.')
    print('To get the code, browse through all of the screens until you get to your redirect_url.')
    print('Google added a query to end that looks like this: ...?code=4/.....&scope=...')
    print('Copy the part between code= and &scope= and add it to the code section in nest.json')
    print()
    print("Go to this URL, answering all of the consent pages, until you get to'"+CONFIG['nest']['redirect_uri']+"':")
    print()
    print(login_url)
    print()
    input('Hit return after you have added the new code into ' + args.config_file)
    get_config(args.config_file)
    get_tokens()
    write_config(args.config_file)
    print('The new configuration:')
    print_config()

def make_chords_vars(old_hash, replace_keys):
    """
    Rename the keys in a hash. If an old key does not
    exist in the new_keys, remove it.
    """
    new_hash = {}
    for old_key, old_val in old_hash.items():
        if old_key in replace_keys:
            new_hash[replace_keys[old_key]] = old_val

    # The chords library wants the vars in a separate dict
    new_hash = {"vars": new_hash}
    return new_hash

if __name__ == '__main__':

  args = arg_parse()
  print("Starting", sys.argv)

  new_keys = {
      'time': 'at',
      'tempC': 'tdry',
      'RH': 'rh'
  }

  get_config(args.config_file)

  # Handle a reporting interval overide.
  report_interval = CONFIG['nest']['report_interval']
  if args.interval:
    report_interval = args.interval

  if VERBOSE:
    print_config()

  # Get a new authorization code, if requested.
  if args.new_code:
    new_code(args)

  # Renewing the tokens is a routine activity.
  # Tokens are good for 60 minutes.
  token_renew(args.config_file)

  if VERBOSE:
    print('The refreshed tokens')
    print_config()

  # Get the avaiable Nest structures.
  # Enable verbose to view them.
  get_structures()

  # Get the Nest devices. For now we will just use the first one listed.
  # Turn on verbose to list all of them.
  device_name = get_devices()

  # Start the CHORDS sender thread
  tochords.startSender()

  # The query loop.
  while (1):
    # Sleep until the next reporting time
    mod_sleep(report_interval)
    nest_data = get_device_stats(device_name)
    # Make a chords variable dict to send to chords
    chords_record = make_chords_vars(nest_data, new_keys)
    # Merge in the chords options
    chords_record.update(CONFIG['chords'])
    # create the chords uri
    uri = tochords.buildURI(CONFIG['chords']['host'], chords_record)
    print(uri)
    # Send it to chords
    if not TEST:
      tochords.submitURI(uri, 10*24*60)

    print(nest_data)
    #print(chords_record)
    token_renew(args.config_file)

