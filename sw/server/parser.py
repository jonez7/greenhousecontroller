import json
import time
import datetime
import db

def ParseRoomData(epochtime, json_data, room):
    ret = []
    avg_humidity    = 0
    avg_temperature = 0
    count           = 0
    sum_humidity    = 0
    sum_temperature = 0
    sum_tgt_humidity    = 0
    sum_tgt_temperature = 0
    heating_time = 0
    cooling_time = 0
    humidifying_time = 0
    reportdata = {}
    for item in json_data[room]["minutes"]:
        count               += 1
        sum_humidity        += item["h"]
        sum_temperature     += item["t"]
        sum_tgt_humidity    += item["th"]
        sum_tgt_temperature += item["tt"]
        heating_time        += item["hec"]
        cooling_time        += item["cc"]
        humidifying_time    += item["huc"]
        if ( count == 15 ):
            avg_humidity        = sum_humidity / count
            avg_temperature     = sum_temperature / count
            avg_tgt_humidity    = sum_tgt_humidity / count
            avg_tgt_temperature = sum_tgt_temperature / count
            reportdata["id"] = room
            reportdata["timestamp"] = epochtime
            reportdata["avg_humidity"] = avg_humidity
            reportdata["avg_temperature"] = avg_temperature
            reportdata["tgt_humidity"] = avg_tgt_humidity
            reportdata["tgt_temperature"] = avg_tgt_temperature
            reportdata["heating_time"] = heating_time
            reportdata["cooling_time"] = cooling_time
            reportdata["humidifiying_time"] = humidifying_time
            reportdata["lights_on_time"] = 0
            reportdata["alarms"] = 0
            sum_humidity     = 0
            sum_temperature  = 0
            heating_time     = 0
            cooling_time     = 0
            humidifying_time = 0
            count            = 0
            epochtime        = epochtime + (15 * 60)
            ret.append(reportdata)
            reportdata={}
    return ret
    
def ReportParser(reportdata):
    ret = []
    try:
        json_data = json.loads(reportdata)
        if (json_data["msg"] == "tehucod report"):
            ts = json_data["ts"]
            epochtime = time.mktime(datetime.datetime.strptime(ts, "%H:%M %d.%m.%Y").timetuple())
            room1data = ParseRoomData(epochtime, json_data, "room1")
            room2data = ParseRoomData(epochtime, json_data, "room2")
            for item in room1data:
                ret.append(item)
            for item in room2data:
                ret.append(item)
            return ret
    except:
        print "Parsing Failed"
        return ret


def ThlsParser(reportdata):
    thlsdata = {}
    try:
        json_data = json.loads(reportdata)
        if (json_data["msg"] == "tehucod report"):
            ts = json_data["ts"]
            epochtime = time.mktime(datetime.datetime.strptime(ts, "%H:%M %d.%m.%Y").timetuple())
            thlsdata["ts"] = epochtime

            thlsdata["s1_temp"] = json_data["thls_report"]["s1_temp"]
            thlsdata["s2_temp"] = json_data["thls_report"]["s2_temp"]
            thlsdata["s3_temp"] = json_data["thls_report"]["s3_temp"]
            thlsdata["s4_temp"] = json_data["thls_report"]["s4_temp"]
            thlsdata["s5_temp"] = json_data["thls_report"]["s5_temp"]
            thlsdata["s1_hum"] = json_data["thls_report"]["s1_hum"]
            thlsdata["s2_hum"] = json_data["thls_report"]["s2_hum"]
            thlsdata["s3_hum"] = json_data["thls_report"]["s3_hum"]
            thlsdata["s4_hum"] = json_data["thls_report"]["s4_hum"]
            thlsdata["s5_hum"] = json_data["thls_report"]["s5_hum"]

            return thlsdata
    except:
        print "Parsing Failed"
        return thlsdata


testdata = """
{
 "msg":"tehucod report",
 "ts":"12:24 31.01.2015",
 "room1": {
 "minutes": [
  {"t":22.48,"h":71.20,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.49,"h":70.90,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.50,"h":70.61,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.50,"h":70.31,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.50,"h":70.11,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.50,"h":69.81,"tt":20.5,"th":80.0,"hec":0,"cc":40,"huc":40},
  {"t":22.50,"h":69.51,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.49,"h":69.21,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.49,"h":68.92,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.48,"h":68.63,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.46,"h":68.34,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.45,"h":68.06,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.44,"h":67.88,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60},
  {"t":22.42,"h":67.61,"tt":20.5,"th":80.0,"hec":0,"cc":40,"huc":40},
  {"t":22.40,"h":67.35,"tt":20.5,"th":80.0,"hec":0,"cc":60,"huc":60}
    ]
  },
  "room2": {
    "minutes": [
  {"t":20.30,"h":63.20,"tt":20.5,"th":79.0,"hec":0,"cc":0,"huc":60},
  {"t":20.23,"h":63.12,"tt":20.5,"th":79.0,"hec":0,"cc":0,"huc":60},
  {"t":20.15,"h":63.05,"tt":20.5,"th":79.0,"hec":0,"cc":0,"huc":60},
  {"t":20.08,"h":63.01,"tt":20.5,"th":79.0,"hec":0,"cc":0,"huc":60},
  {"t":20.03,"h":63.00,"tt":20.5,"th":79.0,"hec":0,"cc":0,"huc":40},
  {"t":19.95,"h":63.01,"tt":20.5,"th":79.0,"hec":20,"cc":0,"huc":60},
  {"t":19.88,"h":63.03,"tt":20.5,"th":79.0,"hec":60,"cc":0,"huc":60},
  {"t":19.80,"h":63.09,"tt":20.5,"th":79.0,"hec":60,"cc":0,"huc":60},
  {"t":19.73,"h":63.17,"tt":20.5,"th":79.0,"hec":60,"cc":0,"huc":60},
  {"t":19.65,"h":63.27,"tt":20.5,"th":79.0,"hec":60,"cc":0,"huc":60},
  {"t":19.58,"h":63.40,"tt":20.5,"th":79.0,"hec":60,"cc":0,"huc":60},
  {"t":19.51,"h":63.55,"tt":20.5,"th":79.0,"hec":60,"cc":0,"huc":60},
  {"t":19.46,"h":63.66,"tt":20.5,"th":79.0,"hec":40,"cc":0,"huc":40},
  {"t":19.38,"h":63.85,"tt":20.5,"th":79.0,"hec":60,"cc":0,"huc":60},
  {"t":19.31,"h":64.06,"tt":20.5,"th":79.0,"hec":60,"cc":0,"huc":60}
  ]
 },
 "thls_report": {
  "s1_temp": 24.932474,
  "s2_temp": 25.932478,
  "s3_temp": 26.932472,
  "s4_temp": 27.932474,
  "s5_temp": 28.932474,
  "s1_hum": 38.416290,
  "s2_hum": 39.416290,
  "s3_hum": 40.416290,
  "s4_hum": 41.416290,
  "s5_hum": 42.416290
 },
 "status_report": {
  "THCtrlConnectionLost": 1,
  "THS1ConnectionLost": 0,
  "THS2ConnectionLost": 0,
  "THSLConnectionLost": 0,
  "room1TempControlFailure": 0,
  "room1HumControlFailure": 1,
  "room1CoolControlFailure": 1,
  "room2TempControlFailure": 1,
  "room2HumControlFailure": 1,
  "room2CoolControlFailure": 0
 }
}
"""
"""
ret = ReportParser(testdata)
print ret

thlsdata = ThlsParser(testdata)
print thlsdata

db.InsertLeakData(thlsdata["ts"],
                  thlsdata["s1_temp"],
                  thlsdata["s1_hum"],
                  thlsdata["s2_temp"],
                  thlsdata["s2_hum"],
                  thlsdata["s3_temp"],
                  thlsdata["s3_hum"],
                  thlsdata["s4_temp"],
                  thlsdata["s4_hum"],
                  thlsdata["s5_temp"],
                  thlsdata["s5_hum"])

data = db.GetDataLeak(100)
print data

for item in ret:
    print item
    db.InsertData(item["id"],
                  item["timestamp"],
                  item["avg_temperature"],
                  item["avg_humidity"],
                  item["tgt_temperature"],
                  item["tgt_humidity"],
                  item["heating_time"],
                  item["cooling_time"],
                  item["humidifiying_time"],
                  item["lights_on_time"],
                  item["alarms"])
"""
