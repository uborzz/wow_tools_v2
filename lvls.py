# -*- coding: utf-8 -*-

# rady

import urllib2 as urllib
import json
import time
from datetime import datetime, timedelta
import urlparse
import re

print urllib.__version__

# PATH TO FILES
key_file = "/var/www/ilvls/ilvls/publickey_2018"
json_file_ilvls = "/var/www/ilvls/ilvls/ilvls.json"

# key_file = "publickey_2018"
# json_file_ilvls = "ilvls.json"


key = open(key_file).read()
base = "https://eu.api.battle.net/wow/character/c'thun/"
guild_base = "https://eu.api.battle.net/wow/guild/c'thun/By%20the%20rage%20of%20my%20balls"

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts= urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )

def guildMembers():
    logkey = '?fields=members&locale=en_US&apikey=' + key
    url = guild_base + logkey
    req = urllib.urlopen(url)
    info = json.loads(req.read())
    # return info['members'][0]
    return [{"name": member['character']['name'],
             "level": member['character']['level'],
             "achievementPoints": member['character']['achievementPoints']} for member in info['members']]

def charItems(name):
    logkey = '?fields=items&locale=en_GB&apikey=' + key
    iri = base + name + logkey
    url = iriToUri(iri)
    req = urllib.urlopen(url)
    info = json.loads(req.read())
    return info

def charSttics(name):
    logkey = '?fields=statistics&locale=en_GB&apikey=' + key
    url = base + name + logkey
    info = json.loads(urllib.urlopen(url).read())
    return info

def main(lck):
    tiempo_refresco = 15  # minutos
    last_update = datetime.now() - timedelta(minutes=tiempo_refresco+1)

    while True:

        if datetime.now() - timedelta(minutes=tiempo_refresco) >= last_update:

            miembros = guildMembers()

            for miembro in miembros:
                try:
                    # ITEM LEVEL...
                    items = charItems(miembro['name'])
                    miembro['ilvl-bags'] = items['items']['averageItemLevel']
                    miembro['ilvl-equipped'] = items['items']['averageItemLevelEquipped']
                    print(miembro)
                except:
                    print(miembro, 'failed')

            lck.acquire()
            with open(json_file_ilvls, 'w+') as f:
                f.write(json.dumps(miembros, ensure_ascii=False).encode('utf-8'))
            lck.release()

            last_update = datetime.now()
            print("File updated", datetime.strftime(last_update, "%H:%M:%S"))

        time.sleep(60)
