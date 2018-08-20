from flask import Flask, render_template
import threading
import json
import lvls

app = Flask(__name__)

# Locks ficheros
lck_ilvls = threading.Lock()

# Path to files
json_file_ilvls = "/var/www/ilvls/ilvls/ilvls.json"

@app.route("/")
def index():
    return "Uborzz flask apps available: /ilvls"

@app.route("/ilvls")
def ilvls():
    lck_ilvls.acquire()
    with open(json_file_ilvls, 'r') as fichero:
        data = json.loads(fichero.read())
    #print(data)
    lck_ilvls.release()
    return render_template('template_ilvls.html', members=data)

app_ilvls = threading.Thread(target=lvls.main, args=(lck_ilvls, ))
app_ilvls.start()

if __name__ == "__main__":
    app.run()
