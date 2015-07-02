#!/usr/bin/python3
import string, re
from os import path
from optparse import OptionParser
import feedparser
import dateutil.parser as dateparser
import datetime

def shorthand(alert_type):

  explode = alert_type.split(" ")
  for i in range(len(explode)):
    explode[i] = shorthand_parser(explode[i])
  return ' '.join(explode)

def shorthand_parser(alert_string):
  return{
    'Advisory' : 'Adv',
    'Warning' : 'Warn',
    'Weather' : 'Wx',
    'Winter' : 'Wint',
    'Stagnation' : 'Stag',
    'Air' : 'Air',
    'Watch' : 'Watch',
    'Flash' : 'Flsh',
    'Flood' : 'Fld'
 }.get(alert_string, "NEW")

#creating flags
optParser = OptionParser()
optParser.add_option("-s", "--short", "--conky", dest="short", action="store_true", help="Display shorthand output instead", default=False)
optParser.add_option("-l", "--loc", dest="location", metavar="XXX###", help="Specifiy currently location Zone")
(options, args) = optParser.parse_args()

use_onset = False
if(options.location is not None):
  loc = options.location
else:
  loc = 'OKZ029'
url = 'http://alerts.weather.gov/cap/wwaatmget.php?x=' + loc
feed = feedparser.parse(url)

if feed.entries[0].title == "There are no active watches, warnings or advisories":
  print("No active alerts.")
else:
  for alert in feed.entries:
    if(options.short):
      alert_type = shorthand(alert.cap_event)
    else:
      alert_type = alert.cap_event
    alert_end = dateparser.parse(alert.cap_expires)
    if("cap_onset" in alert):
      alert_start = dateparser.parse(alert.cap_onset)
    else:
      if(not(re.search(r'\d{6}T\d{4}Z', alert.value) == None)):
        start_time = re.search(r'\d{6}T\d{4}Z', alert.value).group()
        if start_time == "000000T0000Z": #Already started
          alert_start = datetime.datetime.now(alert_end.tzinfo)
        else:
          alert_start = dateparser.parse(start_time).astimezone(alert_end.tzinfo)
      else:
        alert_start = datetime.datetime.now(alert_end.tzinfo)
    if(alert_end.day > datetime.datetime.now(alert_end.tzinfo).day):
      if(options.short):
        alert_string = alert_end.strftime(" %a %I:%M%p")
      else:
        alert_string = alert_end.strftime(" until %a %I:%M %p")
    else:
      if(options.short):
        alert_string = alert_end.strftime(" %I:%M%p")
      else:
        alert_string = alert_end.strftime(" until %I:%M %p")
    if (alert_start > datetime.datetime.now(alert_start.tzinfo)):
      if (alert_start.day > datetime.datetime.now(alert_start.tzinfo).day):
        if(options.short):
          alert_string = alert_start.strftime(" %a %I:%M%p -") + alert_string
        else:
          alert_string = alert_start.strftime(" from %a %I:%M %p") + alert_string
      else:
        if(options.short):
          alert_string = alert_start.strftime(" %I:%M%p -") + alert_string
        else:
          alert_string = alert_start.strftime(" from %I:%M %p") + alert_string
    print(alert_type + alert_string)
