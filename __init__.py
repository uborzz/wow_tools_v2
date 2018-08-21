# -*- coding: utf-8 -*-

# rady

from flask import Flask, render_template
import threading
import json
import lvls

app = Flask(__name__)

# Locks ficheros
lck_ilvls = threading.Lock()

# Path to files
json_file_ilvls = "/var/www/ilvls/ilvls/ilvls.json"
# json_file_ilvls = "ilvls.json"

@app.route("/")
def index():
    return render_template('template_apps.html')

@app.route("/ilvls")
def ilvls():
    lck_ilvls.acquire()
    try:
        with open(json_file_ilvls, 'r') as fichero:
            data = json.loads(fichero.read())
            data = sorted(data, key=lambda k: k['ilvl-equipped'], reverse=True)
    except:
        lck_ilvls.release()
        return "Not working. Prueba más tarde."
    lck_ilvls.release()
    return render_template('template_ilvls.html', members=data)

app_ilvls = threading.Thread(target=lvls.main, args=(lck_ilvls, ))
app_ilvls.start()

if __name__ == "__main__":
    app.run()
