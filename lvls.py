# -*- coding: utf-8 -*-

# rady

import urllib2 as urllib
import json
import time
from datetime import datetime, timedelta
import urlparse
import re

print urllib.__version__

production = True

# PATH TO FILES
key_file = "/var/www/ilvls/ilvls/publickey_2018"
json_file_ilvls = "/var/www/ilvls/ilvls/ilvls.json"
json_file_mithics = "/var/www/ilvls/ilvls/mithics.json"
json_file_dungeonlist = "/var/www/ilvls/ilvls/dungeonlist.json"
json_file_locks = "/var/www/ilvls/ilvls/locks.json"
json_file_uldir_normal = "/var/www/ilvls/ilvls/uldir_normal.json"
json_file_uldir_heroic = "/var/www/ilvls/ilvls/uldir_heroic.json"
json_file_stats_extra_info = "/var/www/ilvls/ilvls/stats_extra_info.json"
json_file_pvp = "/var/www/ilvls/ilvls/pvp.json"

if not production:
    key_file = "publickey_2018"
    json_file_ilvls = "ilvls.json"
    json_file_mithics = "mithics.json"
    json_file_dungeonlist = "dungeonlist.json"
    json_file_locks = "locks.json"
    json_file_uldir_normal = "uldir_normal.json"
    json_file_uldir_heroic = "uldir_heroic.json"
    json_file_stats_extra_info = "stats_extra_info.json"
    json_file_pvp = "pvp.json"

key = open(key_file).read()
base = "https://eu.api.battle.net/wow/character/c'thun/"
guild_base = "https://eu.api.battle.net/wow/guild/c'thun/By%20the%20rage%20of%20my%20balls"


def url_encode_non_ascii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)


def iri_to_uri(iri):
    parts = urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti == 1 else url_encode_non_ascii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )


def guild_members():
    logkey = '?fields=members&locale=en_US&apikey=' + key
    url = guild_base + logkey
    req = urllib.urlopen(url)
    info = json.loads(req.read())
    # return info['members'][0]
    return [{"name": member['character']['name'],
             "level": member['character']['level'],
             "rank": member['rank']} for member in info['members']]


def character_api_request(field, name):
    logkey = '?fields=' + field + '&locale=en_GB&apikey=' + key
    iri = base + name + logkey
    url = iri_to_uri(iri)
    req = urllib.urlopen(url)
    info = json.loads(req.read())
    return info


def lastW():
    actual = datetime.today()
    gap = (actual.weekday()-2)  # Miercoles es dia 2 (0-6)
    if gap < 0:
        gap = gap+7

    lastWeds = actual.replace(hour=9, minute=0, second=0, microsecond=0)
    lastWeds = long(time.mktime(lastWeds.timetuple())-86400*gap)*1000
    # resetDate = long(time.mktime(resetDate.timetuple()))*1000
    print "ULTIMA MIERCOLES: ", lastWeds
    return lastWeds


def formatted_ratio(hit, total):
    hit = int(hit)
    total = int(total)
    if total == 0:
        return "-"
    return "{:.2f}%".format(100 * hit / total)


def main(lck, lck_m, lck_uldir_n, lck_uldir_h, lck_pvp):
    tiempo_refresco = 15  # minutos
    last_update = datetime.now() - timedelta(minutes=tiempo_refresco+1)

    while True:

        if datetime.now() - timedelta(minutes=tiempo_refresco) >= last_update:

            miembros = guild_members()

            # Filtro rango directamente aqui para no pedir demasiada mierda
            miembros = [miembro for miembro in miembros if int(miembro['rank']) <= 2]  # rank 0 GM, 1 ofic. ...
            lastWeds = lastW()

            locks_miembros = list()
            pvp_chart = list()
            counter = 0

            if not production: miembros = miembros[5:8]  # tests
            print("guild_members to process:", [miembro['name'] for miembro in miembros])
            for miembro in miembros:

                counter = counter + 1
                print('> Counting dofito {} of {}...'.format(str(counter), len(miembros)))

                # iLvls
                try:
                    # ITEM LEVEL...
                    items = character_api_request("items", miembro['name'])
                    miembro['ilvl-bags'] = items['items']['averageItemLevel']
                    miembro['ilvl-equipped'] = items['items']['averageItemLevelEquipped']
                    miembro['artifact-lvl'] = items['items']['neck']['azeriteItem']['azeriteLevel']
                    # miembro['achievement-points'] = 0  ## initialize achievement points
                except:
                    print(miembro, 'failed in iLvl')


                # dofilock
                try:

                    stats = character_api_request("statistics", miembro['name'])

                    # MYTHICS...
                    exp_stats = stats['statistics']['subCategories'][5]['subCategories'][7]['statistics']
                    all_dungeons = [dung for dung in exp_stats if "mythic" in dung['name'].lower()]  # todas kills, OJO tambien raids
                    for dung in all_dungeons:
                        dung['name'] = json.dumps(dung['name']).split('(Mythic ')[1][:-2]

                    dungeons_locked = [dung for dung in all_dungeons if dung['lastUpdated'] > lastWeds]

                    # ULDIR...
                    uldir_normal = [dung for dung in exp_stats if "uldir" in dung['name'].lower() if "normal" in dung['name'].lower()]
                    uldir_heroic = [dung for dung in exp_stats if "uldir" in dung['name'].lower() if "heroic" in dung['name'].lower()]
                    for dung in uldir_normal:
                        dung['name'] = json.dumps(dung['name']).split('kills')[0][1:-1]
                    for dung in uldir_heroic:
                        dung['name'] = json.dumps(dung['name']).split('kills')[0][1:-1]

                    ulduir_normal_locked = [dung for dung in uldir_normal if dung['lastUpdated'] > lastWeds]
                    ulduir_heroic_locked = [dung for dung in uldir_heroic if dung['lastUpdated'] > lastWeds]

                    locks_miembros.append({"name": miembro['name'], "rank": miembro['rank'], "locks": dungeons_locked,
                                          "uldir_normal": ulduir_normal_locked, "uldir_heroic": ulduir_heroic_locked})

                    # # More INFO from statistics
                    # miembro['achievement-points'] = stats['achievementPoints']
                    print(miembro)

                except:
                    print('>>>', miembro, 'failed in statistics')


                # pvp
                try:
                    pvp = character_api_request("pvp", miembro['name'])

                    pvp_member = dict()
                    pvp_member['name'] = pvp['name']
                    pvp_member['2v2'] = pvp['pvp']['brackets']['ARENA_BRACKET_2v2']
                    pvp_member['3v3'] = pvp['pvp']['brackets']['ARENA_BRACKET_3v3']

                    pvp_member['2v2']['week_ratio'] = formatted_ratio(pvp_member['2v2']['weeklyWon'], pvp_member['2v2']['weeklyPlayed'])
                    pvp_member['2v2']['season_ratio'] = formatted_ratio(pvp_member['2v2']['seasonWon'], pvp_member['2v2']['seasonPlayed'])

                    pvp_member['3v3']['week_ratio'] = formatted_ratio(pvp_member['3v3']['weeklyWon'], pvp_member['3v3']['weeklyPlayed'])
                    pvp_member['3v3']['season_ratio'] = formatted_ratio(pvp_member['3v3']['seasonWon'], pvp_member['3v3']['seasonPlayed'])

                    pvp_chart.append(pvp_member)
                except Exception as e:
                    print('>>>', miembro, 'failed in pvp')
                    print(str(e))

            lck.acquire()
            print("Pillo")
            with open(json_file_ilvls, 'w+') as f:
                f.write(json.dumps(miembros, ensure_ascii=False).encode('utf-8'))
                print(miembros)
            lck.release()
            print("Suelto")

            dungeons = [dung['name'] for dung in all_dungeons]  # mithics
            bosses_uldir_normal = [boss['name'] for boss in uldir_normal]
            bosses_uldir_heroic = [boss['name'] for boss in uldir_heroic]

            with open(json_file_dungeonlist, 'w+') as f:
                dungeons = [dung for dung in dungeons if dungeons.count(dung) is 1] # filtra uldir mithics. chapu
                f.write(json.dumps(dungeons))
            with open(json_file_mithics, 'w+') as f:
                f.write(json.dumps(locks_miembros, ensure_ascii=False).encode('utf-8'))

            uldir_normal_players_locked = {boss: list() for boss in bosses_uldir_normal}
            uldir_heroic_players_locked = {boss: list() for boss in bosses_uldir_heroic}
            dungeon_players_locked = {dungeon: list() for dungeon in dungeons}
            for player in locks_miembros:
                for lock in player['locks']:
                    dungeon_players_locked[lock['name']].append(player['name'])
                for lock in player['uldir_normal']:
                    uldir_normal_players_locked[lock['name']].append(player['name'])
                for lock in player['uldir_heroic']:
                    uldir_heroic_players_locked[lock['name']].append(player['name'])

            lck_m.acquire()
            with open(json_file_locks, 'w+') as f:
                f.write(json.dumps(dungeon_players_locked, ensure_ascii=False).encode('utf-8'))
            lck_m.release()
            print locks_miembros

            lck_uldir_n.acquire()
            with open(json_file_uldir_normal, 'w+') as f:
                f.write(json.dumps(uldir_normal_players_locked, ensure_ascii=False).encode('utf-8'))
            lck_uldir_n.release()

            lck_uldir_h.acquire()
            with open(json_file_uldir_heroic, 'w+') as f:
                f.write(json.dumps(uldir_heroic_players_locked, ensure_ascii=False).encode('utf-8'))
            lck_uldir_h.release()

            lck_pvp.acquire()
            with open(json_file_pvp, 'w+') as f:
                f.write(json.dumps(pvp_chart, ensure_ascii=False).encode('utf-8'))
            lck_pvp.release()

            last_update = datetime.now()
            print("File updated", datetime.strftime(last_update, "%H:%M:%S"))

        time.sleep(60)
