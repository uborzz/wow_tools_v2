# -*- coding: utf-8 -*-

# rady

from flask import Flask, render_template
import threading
import json
import lvls

app = Flask(__name__)

# Locks ficheros
lck_ilvls = threading.Lock()
lck_mythics = threading.Lock()
lck_uldir_normal = threading.Lock()
lck_uldir_heroic = threading.Lock()

# PATH TO FILES
json_file_ilvls = "/var/www/ilvls/ilvls/ilvls.json"
json_file_locks = "/var/www/ilvls/ilvls/locks.json"
json_file_uldir_normal = "/var/www/ilvls/ilvls/uldir_normal.json"
json_file_uldir_heroic = "/var/www/ilvls/ilvls/uldir_heroic.json"

json_file_ilvls = "ilvls.json"
json_file_locks = "locks.json"
json_file_uldir_normal = "uldir_normal.json"
json_file_uldir_heroic = "uldir_heroic.json"


@app.route("/")
def index():
    return render_template('template_apps.html')

@app.route("/ilvls")
def ilvls():
    try:
        lck_ilvls.acquire()
        with open(json_file_ilvls, 'r') as fichero:
            data = json.loads(fichero.read())
        lck_ilvls.release()
        filtered = [miembro for miembro in data if int(miembro['rank']) <= 1]  # rank 0 GM, 1 ofic. ...
        ordenado = sorted(filtered, key=lambda k: k['ilvl-equipped'], reverse=True)
    except IOError:
        lck_mythics.release()
        return "Not working. Prueba más tarde."
    except Exception as e:
        print(str(e))
        return "Not working. Prueba más tarde."
    return render_template('template_ilvls.html', members=ordenado)

@app.route("/locks")
def locks():
    return peticion_tipo_locks(json_file_locks, lck_mythics, "Mythics")

@app.route("/uldir_normal")
def uldirn():
    return peticion_tipo_locks(json_file_uldir_normal, lck_uldir_normal, "Uldir Normal")

@app.route("/uldir_heroic")
def uldirh():
    return peticion_tipo_locks(json_file_uldir_heroic, lck_uldir_heroic, "Uldir Heroic")

def peticion_tipo_locks(fichero, lck, titulo=""):
    try:
        lck.acquire()
        with open(fichero, 'r') as fichero:
            data = json.loads(fichero.read())
        lck.release()
        for key in data.keys():
            data[key] = tuple(sorted(data[key]))
    except IOError:
        lck.release()
        return "Not working. Prueba más tarde."
    except Exception as e:
        print(str(e))
        return "Not working. Prueba más tarde."
    return render_template('template_locks.html', dungeons=data, titulo=titulo)


app_ilvls = threading.Thread(target=lvls.main, args=(lck_ilvls, lck_mythics, lck_uldir_normal, lck_uldir_heroic))
app_ilvls.start()

if __name__ == "__main__":
    app.run()
