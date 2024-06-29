#!/usr/bin/python3

import requests
import json
import pprint
import time
import datetime
from icalendar import Calendar, Event
import argparse
from flask import Flask, make_response, render_template

# {
#     "predictions": [
#         {
#             "t": "2018-06-27 05:50",
#             "type": "L",
#             "v": "-0.031"
#         }
#     ]
# }

#cal['dtstart'] = '20050404T080000'

#8469198 - Stamford Harbor, CT
#8517394 - Barren Island, Rockaway Inlet
#8532337 - Belmar, NJ
#8515186 - Fire Island

flask_app = Flask("tidecal")


parser = argparse.ArgumentParser(prog='tidecal',
                                 description='Take a NOAA station and out put tide info in iCal format',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog='''Some stations are

8469198 - Stamford Harbor, CT
8517394 - Barren Island, Rockaway Inlet
8532337 - Belmar, NJ
8515186 - Fire Island

Find more stations at https://tidesandcurrents.noaa.gov/'''
                                 )


@flask_app.route('/tidecal/', methods=['GET','POST'])
def station_id():
    return render_template('station.html')

parser.add_argument('station',nargs='?',default='8469198', help='The station id to get tide data for.')

args=parser.parse_args()

station=args.station

@flask_app.route("/tidecal/<station>", methods=['GET'])
def get_tide_ics(station):
  begindate = datetime.date.today() - datetime.timedelta(days=7)
  begindate = begindate.strftime('%Y%m%d')
  enddate = datetime.date.today() +  datetime.timedelta(days=90)
  enddate = enddate.strftime('%Y%m%d')
  
  
  
  #set header token:cvuMpmiyEMeEdgQyUKUsWhCemxSyssAO
  
  
  # get name/location info
  
  loc = requests.get(f"https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{station}.json")
  
  locname = loc.json()['stations'][0]["name"]
  locstate = loc.json()['stations'][0]["state"]
  
  
  
  payload = {'product': 'predictions', 'application': 'NOS.COOPS.TAC.WL', 'begin_date': begindate, 'end_date': enddate, 'datum': 'MLLW', 'station': station, 'time_zone': 'GMT', 'units': 'english', 'interval': 'hilo', 'format': 'json'}
  
  r = requests.get('https://tidesandcurrents.noaa.gov/api/datagetter', params=payload)
  
  tides = r.json()
  #print(tides)
  cal = Calendar()
  #cal.add('prodid', '-//my tide script')
  #cal.add('version', '0.99')
  cal.add('X-WR-CALNAME', f'{locname}, {locstate}')
  
  for forecast in tides['predictions']:
    time = forecast['t']
    tide = forecast['type']
    height = forecast['v']
    d = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M").strftime('%Y%m%dT%H%M00Z')
    if tide == 'H':
      longt = "High Tide"
    elif tide == 'L':
      longt = "Low Tide"
    event = Event()
    event['dtstart'] = d
    event['summary'] = longt
    event['dtend'] = d
    event['location'] = f"{locname}, {locstate}"
    cal.add_component(event)
  response=make_response(cal.to_ical().decode('utf-8'))
  response.headers['Content-Type'] = 'text/calendar'
  response.headers['Content-Disposition'] = f'inline; filename="{station}.ics"'
  return(response)
  
if __name__ == "__main__":
    flask_app.run(host="127.0.0.1", port=8080, debug=True)