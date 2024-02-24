import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import datetime
import time
import urllib.request
import json

app = FastAPI()

app.data = dict()
app.powerdata = dict()

with open("/home/bob/solarapi/devpower.json") as fh:
        powerdict = json.load(fh)

app.belltime=0
app.lastbell = "Never"

class SetPower(BaseModel):
    power : int
    energy : float

class PowerRecord:
    nowpower : int
    maxpower : int
    nowtime : int
    maxtime : int
    starttime : int
    startenergy : float
    nowenergy : float
    comment : str

@app.get("/reset")
def reset():
    app.data = dict()

@app.get("/log")
def log():
    t = time.time()
    td = time.strftime('%Y%m%d',time.localtime(t))
    logfile = time.strftime('/home/bob/log/solar-summary-%Y.log',time.localtime(t))
    for k in app.data.keys():
      ls = "{ 'date' : '"+str(td)
      ls = ls +"', 'serial' : '"+k
      ls = ls +"', 'energy' : '"+str(app.data[k].nowenergy-app.data[k].startenergy)
      ls = ls +"', 'starttime' : '"+time.strftime('%H:%M:%S', time.localtime(app.data[k].starttime))
      ls = ls +"', 'endtime' : '"+time.strftime('%H:%M:%S', time.localtime(app.data[k].nowtime))
      ls = ls +"', 'maxpower' : '"+str(app.data[k].maxpower)
      ls = ls +"', 'maxtime' : '"+time.strftime('%H:%M:%S', time.localtime(app.data[k].maxtime))
      ls = ls +"' }"
      with open(logfile, "a") as fh:
        fh.write(ls+"\n")
        fh.close()

@app.get("/getserials")
def getserials():
    res = ""
    for k in app.data.keys():
        if res == "":
            res = k
        else:
            res=res+" "+k
    return res 
#    return 'fake 32E5DDEA banana'

@app.get("/readpower/{serialnumber}")
def readpower(serialnumber: str):
    if serialnumber in app.data:
        i = serialnumber
        return {"serial" : i, "comment" : app.data[i].comment, "nowtime" : time.strftime('%H:%M:%S', time.localtime(app.data[i].nowtime)), "starttime" : time.strftime('%H:%M:%S', time.localtime(app.data[i].starttime)), "power" : app.data[i].nowpower, "startenergy" : app.data[i].startenergy, "nowenergy" : app.data[i].nowenergy, "max" : app.data[i].maxpower, "maxtime" : time.strftime('%H:%M:%S', time.localtime(app.data[i].maxtime))}
    else:
        return {"serial" : serialnumber}

@app.patch("/setpower/{serialnumber}")
def setpower(serialnumber: str, value : SetPower):
    newdata=PowerRecord()
    newdata.nowpower=value.power
    newdata.maxpower=value.power
    newdata.nowtime=time.time()
    newdata.maxtime=time.time()
    newdata.comment=""
    newdata.startenergy=0.0
    newdata.nowenergy=0.0
    t = time.time()
    ts = time.strftime('%H:%M:%S',time.localtime(t))
    logfile = time.strftime("/home/bob/log/solar-"+serialnumber+'-%Y%m%d.log',time.localtime(t))
    with open(logfile, "a") as fh:
        fh.write(ts+" "+str(value.power)+"\n")
        fh.close()
    if serialnumber not in app.data:
        app.data[serialnumber] = newdata
        app.data[serialnumber].startenergy=value.energy
        app.data[serialnumber].nowenergy=value.energy
        app.data[serialnumber].maxpower=value.power
        app.data[serialnumber].maxtime=t
        app.data[serialnumber].starttime=t
        app.data[serialnumber].comment=""
    else:
        app.data[serialnumber].nowpower=value.power
        app.data[serialnumber].nowtime=t
        app.data[serialnumber].nowenergy=value.energy
        for i in powerdict:
          if (value.power >= i['power']) and (app.data[serialnumber].maxpower < i['power']):
            app.data[serialnumber].comment += i['name']+" at "+ts+"<p>"
            urllib.request.urlopen(i['url'])
        if value.power > app.data[serialnumber].maxpower:
                   app.data[serialnumber].maxpower=value.power
                   app.data[serialnumber].maxtime=t
    return {}



@app.get("/doorbell")
def bell():
    t = int(time.time())
    if (t > app.belltime+30):
        app.belltime = t
        app.lastbell = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
        logfile = time.strftime('/home/bob/log/doorbell-%Y%m.log')
        with open(logfile, "a") as fh:
            fh.write("Doorbell at "+app.lastbell+"\n")
            fh.close()
    return(app.lastbell)

@app.get("/readbell")
def readdoorbell():
    return(app.lastbell)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host='0.0.0.0', reload=True)

