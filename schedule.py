import iksm
import json
import os, re, sys
from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime
from base64 import urlsafe_b64decode

def sign_in():
  # 認証用のURL取得
  oauthURL = iksm.get_session_token_code()
  print("Navigate to this URL in your browser:")
  print(oauthURL)
  print("Log in, right click the \"Select this account\" button, copy the link address, and paste it below:")
  while True:
    try:
      url_scheme = input("")
      iksm.get_cookie(url_scheme)
      break
    except KeyboardInterrupt:
      sys.exit(1)
    except AttributeError:
      pass
    except KeyError:
      pass

def to_srcal(schedule):
  cal = Calendar()
  cal.add('prodid', '-//Salmon Run Rotation//salmon-stats.ink//')
  cal.add('version', '2.0')

  for entry in schedule:
    dstart      = entry['startTime']
    dend        = entry['endTime']
    location    = entry['setting']['coopStage']['name']
    location_id = entry['setting']['coopStage']['id']
    weapons     = entry['setting']['weapons']

    event = Event()
    event.add('location', vText(location))
    event.add('summary', vText("Salmon Run NW: " + location))
    w = []
    for weapon in weapons:
      w.append(weapon['name'])
    event.add('description', vText("Weapon set: " + ", ".join(w)))
    # we are cheating a bit for the creation time
    event.add('dtstamp', datetime.fromisoformat(dstart))
    event.add('dtstart', datetime.fromisoformat(dstart))
    event.add('dtend', datetime.fromisoformat(dend))
    event.add('uid', dstart + "@" + urlsafe_b64decode(location_id).decode(encoding='utf-8'))
    cal.add_component(event)

  with open("schedule.ics", mode="wb") as f:
    f.write(cal.to_ical())


if __name__=='__main__':
  try:
    full_schedule = iksm.get_schedule()
    sr_schedule = full_schedule['coopGroupingSchedule']['regularSchedules']['nodes']
    to_srcal(sr_schedule)


  except FileNotFoundError:
    sign_in()
