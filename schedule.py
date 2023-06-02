import iksm
import json
import os, re, sys
from icalendar import Calendar, Event, vCalAddress, vText, vUri
from datetime import datetime
from base64 import urlsafe_b64decode
from os.path import exists
import urllib.request
import gzip

def sign_in() -> None:
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

stageToURI = {
  "CoopStage-1" : "be584c7c7f547b8cbac318617f646680541f88071bc71db73cd461eb3ea6326e_0.png", # Spawning Grounds
  "CoopStage-2" : "3418d2d89ef84288c78915b9acb63b4ad48df7bfcb48c27d6597920787e147ec_0.png", # Sockeye Station
  "CoopStage-3" : "",
  "CoopStage-4" : "",
  "CoopStage-5" : "",
  "CoopStage-6" : "1a29476c1ab5fdbc813e2df99cd290ce56dfe29755b97f671a7250e5f77f4961_0.png", # Marooner Bay
  "CoopStage-7" : "f1e4df4cff1dc5e0acc66a9654fecf949224f7e4f6bd36305d4600ac3fa3db7b_0.png", # Gone Fission Hydroplant
  "CoopStage-8" : "0e05d4caa34089a447535708370286f4ee6068661359b4d7cf6c319863424f84_0.png" # Jammin' Salmon Junction
}

def stage_to_uri(stagename:str) -> str:
  if stagename in stageToURI:
    return "https://salmon-stats.ink/images/coop_stage/" + stageToURI[stagename]
  return ""

# yes, we have duplication of efforts here, but we only have 5 items
def srjson_to_arrays(coop_infos: dict) -> dict:
  sr_schedule = { "regularEvents": [], "specialEvents" : []}

  for entry in sorted(coop_infos['regularSchedules']['nodes'], key=lambda x:x['startTime']):
    sr_schedule['regularEvents'].append(entry)

  for entry in sorted(coop_infos['bigRunSchedules']['nodes'], key=lambda x:x['startTime']):
    sr_schedule['specialEvents'].append(entry)

  return sr_schedule


def to_srcal(sorted_schedule:dict, outfile:str="schedule.ics") -> None:
  cal = Calendar()
  cal.add('prodid', '-//Salmon Run Rotation//salmon-stats.ink//')
  cal.add('version', '2.0')

  grizz = vCalAddress('MAILTO:bear03@salmon-stats.ink')
  grizz.params['cn'] = vText('Mr. Grizz')
  grizz.params['role'] = vText('CHAIR')

  for entry in sorted_schedule['regularEvents']:
    dstart      = entry['startTime']
    dend        = entry['endTime']
    location    = entry['setting']['coopStage']['name']
    location_id = entry['setting']['coopStage']['id']
    weapons     = entry['setting']['weapons']
    decoded_location_id = urlsafe_b64decode(location_id).decode(encoding='utf-8')

    stage = vCalAddress(vUri(stage_to_uri(decoded_location_id)))
    stage.params['fmttype'] = vText('image/png')
    stage.params['display'] = vText('FULLSIZE')
    stage.params['value'] = vText('URI')

    event = Event()
    event.add('organizer', grizz)
    event.add('location', vText(location))
    event.add('summary', vText("SRNW: " + location))
    event.add('image', stage)
    event.add('description', vText("Weapon set: " + ", ".join(map(lambda w:w['name'], weapons))))
    # we are cheating a bit for the creation time
    event.add('dtstamp', datetime.fromisoformat(dstart))
    event.add('dtstart', datetime.fromisoformat(dstart))
    event.add('dtend', datetime.fromisoformat(dend))
    event.add('uid', dstart + "@" + urlsafe_b64decode(location_id).decode(encoding='utf-8'))
    cal.add_component(event)

  for entry in sorted_schedule['specialEvents']:
    dstart      = entry['startTime']
    dend        = entry['endTime']
    location    = entry['setting']['coopStage']['name']
    location_id = entry['setting']['coopStage']['id']
    weapons     = entry['setting']['weapons']
    decoded_location_id = urlsafe_b64decode(location_id).decode(encoding='utf-8')

    event = Event()
    event.add('organizer', grizz)
    event.add('location', vText(location))
    event.add('summary', vText("BigRun: " + location))
    event.add('description', vText("Weapon set: " + ", ".join(map(lambda w:w['name'], weapons))))
    # we are cheating a bit for the creation time
    event.add('dtstamp', datetime.fromisoformat(dstart))
    event.add('dtstart', datetime.fromisoformat(dstart))
    event.add('dtend', datetime.fromisoformat(dend))
    event.add('uid', dstart + "@" + decoded_location_id)
    cal.add_component(event)
  with open(outfile, mode="wb") as f:
    f.write(cal.to_ical())
    

def load_images(coop_infos:dict) -> None:
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

def update_complete_schedule(coop_infos:dict) -> None:
  fname = "complete_schedule.json.gz"
  if os.path.isfile(fname):
    with gzip.open(fname, "rt", encoding='utf-8') as f:
      complete_schedule = json.load(f)
  else:
    complete_schedule = { "regularEvents": [], "specialEvents" : []}

  for entry in sorted(coop_infos['regularSchedules']['nodes'], key=lambda x:x['startTime']):
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

  for entry in sorted(coop_infos['bigRunSchedules']['nodes'], key=lambda x:x['startTime']):
    complete_schedule['specialEvents'].append(entry)

  to_srcal(complete_schedule, outfile="complete_schedule.ics")

  with gzip.open(fname, "wt", compresslevel=9, encoding='utf-8') as f:
    json.dump(complete_schedule, f)

if __name__=='__main__':
  try:
    full_schedule = iksm.get_schedule()
    sorted_schedule = srjson_to_arrays(full_schedule['coopGroupingSchedule'])
    to_srcal(sorted_schedule)

  except FileNotFoundError:
    sign_in()

  load_images(full_schedule['coopGroupingSchedule'])
  update_complete_schedule(full_schedule['coopGroupingSchedule'])
