import iksm
import json
import os, re, sys
from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime
from base64 import urlsafe_b64decode
from os.path import exists
import urllib.request
import gzip

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
    

def load_images(coop_infos):
  if not os.path.isdir("images"):
    os.mkdir("images")
    os.mkdir("images/coop_weapon")
    os.mkdir("images/coop_stage")
    os.mkdir("images/coop_stage_thb")

  for entry in coop_infos['regularSchedules']['nodes']:
    thumbnailstageurl = entry['setting']['coopStage']['thumbnailImage']['url']
    thumbnailsavpath = f"images/coop_stage_thb/{thumbnailstageurl.split('/')[-1].split('?')[0]}"
    if not exists(thumbnailsavpath):
      print(f"Fetching stage {thumbnailsavpath}")
      urllib.request.urlretrieve(thumbnailstageurl, thumbnailsavpath)

    imagestageurl = entry['setting']['coopStage']['image']['url']
    imagesavpath = f"images/coop_stage/{imagestageurl.split('/')[-1].split('?')[0]}"
    if not exists(imagesavpath):
      print(f"Fetching stage thumbnail {imagesavpath}")
      urllib.request.urlretrieve(imagestageurl, imagesavpath)

    for weapon in entry['setting']['weapons']:
      weaponurl = weapon['image']['url']
      weaponsavpath = f"images/coop_weapon/{weaponurl.split('/')[-1].split('?')[0]}"
      if not exists(weaponsavpath):
        print(f"Fetching weapon {weapon['name']} {weaponsavpath}")
        urllib.request.urlretrieve(weaponurl, weaponsavpath)

def update_complete_schedule(coop_infos):
  fname = "complete_schedule.json.gz"
  if os.path.isfile(fname):
    with gzip.open(fname, "rt", encoding='utf-8') as f:
      complete_schedule = json.load(f)
  else:
    complete_schedule = { "regularEvents": [], "specialEvents" : []}

  for entry in coop_infos['regularSchedules']['nodes']:
    # rewrite the URLs in the entry
    url = entry['setting']['coopStage']['image']['url'].split('/')[-1].split('?')[0]
    entry['setting']['coopStage']['image']['url'] = url
    url = entry['setting']['coopStage']['thumbnailImage']['url'].split('/')[-1].split('?')[0]
    entry['setting']['coopStage']['thumbnailImage']['url'] = url
    for weapon in entry['setting']['weapons']:
      weaponurl = weapon['image']['url'].split('/')[-1].split('?')[0]
      weapon['image']['url'] = weaponurl

    if entry not in complete_schedule['regularEvents']:
      # TODO url filtering like above
      complete_schedule['regularEvents'].append(entry)

  for entry in coop_infos['bigRunSchedules']['nodes']:
    complete_schedule['specialEvents'].append(entry)

  with gzip.open(fname, "wt", compresslevel=9, encoding='utf-8') as f:
    json.dump(complete_schedule, f)

if __name__=='__main__':
  try:
    full_schedule = iksm.get_schedule()
    to_srcal(full_schedule['coopGroupingSchedule'])

  except FileNotFoundError:
    sign_in()

  load_images(full_schedule['coopGroupingSchedule'])
  update_complete_schedule(full_schedule['coopGroupingSchedule'])
