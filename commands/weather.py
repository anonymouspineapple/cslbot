# Copyright (C) 2013-2014 Fox Wilson, Peter Foley, Srijay Kasturi, Samuel Damashek, James Forcier and Reed Koser
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import re
from requests import get
from helpers.orm import Weather_prefs
from helpers.command import Command


def get_default(nick, session, send):
    location = session.query(Weather_prefs.location).filter(Weather_prefs.nick == nick).scalar()
    if location is None:
        # default to TJHSST
        location = '22312'
        send("No default location for %s, defaulting to TJ (%s)." % (nick, location))
    return location


def valid_location(location, apikey):
    data = get('http://api.wunderground.com/api/%s/conditions/q/%s.json' % (apikey, location)).json()
    return 'current_observation' in data


def set_default(nick, location, session, send, apikey):
    """Sets nick's default location to location."""
    if valid_location(location, apikey):
        send("Setting default location")
        default = session.query(Weather_prefs).filter(Weather_prefs.nick == nick).first()
        if default is None:
            default = Weather_prefs(nick=nick, location=location)
            session.add(default)
        else:
            default.location = location
    else:
        send("Invalid or Ambiguous Location")


def get_weather(msg, send, apikey):
    if msg.startswith("-"):
        data = get('http://api.wunderground.com/api/%s/conditions/q/%s.json' % (apikey, msg[1:])).json()
        if 'current_observation' not in data:
            send("Invalid or Ambiguous Location")
            return False
        data = {'display_location': {'full': msg[1:]},
                'weather': 'Sunny', 'temp_f': '94.8', 'relative_humidity': '60%', 'pressure_in': '29.98', 'wind_string': 'Calm'}
        forecastdata = {'conditions': 'Thunderstorms... Extreme Thunderstorms... Plague of Insects... The Rapture... Anti-Christ',
                        'high': {'fahrenheit': '-3841'}, 'low': {'fahrenheit': '-6666'}}
    else:
        data = get('http://api.wunderground.com/api/%s/conditions/q/%s.json' % (apikey, msg)).json()
        forecastdata = get('http://api.wunderground.com/api/%s/forecast/q/%s.json' % (apikey, msg)).json()
        if 'current_observation' in data:
            data = data['current_observation']
        else:
            send("Invalid or Ambiguous Location")
            return False
        forecastdata = forecastdata['forecast']['simpleforecast']['forecastday'][0]
    send("Current weather for %s:" % data['display_location']['full'])
    current = '%s, Temp: %s, Humidity: %s, Pressure: %s", Wind: %s' % (
        data['weather'],
        data['temp_f'],
        data['relative_humidity'],
        data['pressure_in'],
        data['wind_string'])
    forecast = '%s, High: %s, Low: %s' % (
        forecastdata['conditions'],
        forecastdata['high']['fahrenheit'],
        forecastdata['low']['fahrenheit'])
    send(current)
    send("Forecast: " + forecast)
    return True


@Command(['weather', 'bjones'], ['nick', 'config', 'db', 'name'])
def cmd(send, msg, args):
    """Gets the weather.
    Syntax: !weather <location|set default>
    """
    apikey = args['config']['api']['weatherapikey']
    match = re.match("set (.*)", msg)
    if match:
        set_default(args['nick'], match.group(1), args['db'], send, apikey)
        return
    nick = args['nick'] if args['name'] == 'weather' else '`bjones'
    if not msg:
        msg = get_default(nick, args['db'], send)
    get_weather(msg, send, apikey)
