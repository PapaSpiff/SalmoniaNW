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

def to_srcal(coop_infos):
  cal = Calendar()
  cal.add('prodid', '-//Salmon Run Rotation//salmon-stats.ink//')
  cal.add('version', '2.0')

  grizz = vCalAddress('MAILTO:bear03@salmon-stats.ink')
  grizz.params['cn'] = vText('Mr. Grizz')
  grizz.params['role'] = vText('CHAIR')

  for entry in coop_infos['regularSchedules']['nodes']:
    dstart      = entry['startTime']
    dend        = entry['endTime']
    location    = entry['setting']['coopStage']['name']
    location_id = entry['setting']['coopStage']['id']
    weapons     = entry['setting']['weapons']

    event = Event()
    event.add('organizer', grizz)
    event.add('location', vText(location))
    event.add('summary', vText("SRNW: " + location))
    event.add('description', vText("Weapon set: " + ", ".join(map(lambda w:w['name'], weapons))))
    # we are cheating a bit for the creation time
    event.add('dtstamp', datetime.fromisoformat(dstart))
    event.add('dtstart', datetime.fromisoformat(dstart))
    event.add('dtend', datetime.fromisoformat(dend))
    event.add('uid', dstart + "@" + urlsafe_b64decode(location_id).decode(encoding='utf-8'))
    cal.add_component(event)

  for entry in coop_infos['bigRunSchedules']['nodes']: 
    dstart      = entry['startTime']
    dend        = entry['endTime']
    location    = entry['setting']['coopStage']['name']
    location_id = entry['setting']['coopStage']['id']
    weapons     = entry['setting']['weapons']

    event = Event()
    event.add('organizer', grizz)
    event.add('location', vText(location))
    event.add('summary', vText("BigRun: " + location))
    event.add('description', vText("Weapon set: " + ", ".join(map(lambda w:w['name'], weapons))))
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
    to_srcal(full_schedule['coopGroupingSchedule'])


  except FileNotFoundError:
    sign_in()
