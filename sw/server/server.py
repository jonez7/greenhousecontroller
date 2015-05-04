import tornado.ioloop
import tornado.web
import currentstatus
import json
import parser
import db
import time
import uuid
import hashlib
import settings
 
def hash_password(password):
    # uuid is used to generate a random number
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt
    
def check_password(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user", max_age_days=1)


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        f = open("index_server.html", "r")
        data = f.read()
        f.close()
        data = data.replace("<!--STATS-->", '<a href="stats.html"><img src="/images/graph.png" title="Tilastot"></a>')

        self.write(data)

class LogoutHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        f = open("logout.html", "r")
        data = f.read()
        f.close()
        self.clear_cookie("user")
        self.write(data)


    
def MeasHandler(action):
    
    ret  = '''{'''
    ret += '''"datetime": "''' + str(currentstatus.last_response) + '''",'''
    ret += '''"temperature": ''' + str(currentstatus.temperature) + ''','''
    ret += '''"humidity": ''' + str(currentstatus.humidity) + ''','''
    ret += '''"cooling": ''' + str(currentstatus.cooling) + ''','''
    ret += '''"heating": ''' + str(currentstatus.heating)
    ret += '''}'''
    print ret
    return ret

class CgiHandler(tornado.web.RequestHandler):
    def get(self):

        print(self.request.uri)

        pageId = self.get_argument("page", None, True)
        action = self.get_argument("action", None, True)
        
        if "settings" == pageId:
            f = open("settings.html", "r")
            data = f.read()
            f.close()
            self.write(data)
        elif "service" == pageId:
            f = open("service.html", "r")
            data = f.read()
            f.close()
            self.write(data)
        elif "pass" == pageId:
            f = open("pass.html", "r")
            data = f.read()
            f.close()
            self.write(data)
        elif "settingsdata" == pageId:
            bufferedItem = "page=" + pageId + "&action=" + action + "&source=remote"
            currentstatus.actionqueue.append(bufferedItem)
            ret = NewSettingsHandler(action)
            print ret
            self.write(ret)
        elif "mainpage" == pageId:
            bufferedItem = "page=" + pageId + "&action=" + action + "&source=remote"
            currentstatus.actionqueue.append(bufferedItem)
            ret = MeasHandler(action)
            print ret
            self.write(ret)

class ReportHandler(tornado.web.RequestHandler):
    def post(self):  
        print("report:")
        f = open("report.log", "a")
        f.write(self.request.body)
        f.close()
        ret = parser.ReportParser(self.request.body)
        for item in ret:
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

        thlsdata = parser.ThlsParser(self.request.body)

        self.write("report stored successfully")

class RequestHandler(tornado.web.RequestHandler):
    def get(self):
        if (len(currentstatus.actionqueue) == 0):
            self.write("page=none&action=none&source=remote")
        else: 
            action = currentstatus.actionqueue.pop(0)
            self.write(action)

class ResponseHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("response handled")

    def post(self):  
        print("response received")

        currentstatus.last_response_ts = int(time.time())

        data = self.request.body
        print data
        jsonstr = "{" + data.split("{")[1]
        
        json_data=json.loads(jsonstr)

        for key, value in json_data.iteritems():
#            print key, value

            if "datetime" == key:
                currentstatus.last_response = value

            if "room1_acboost_max_temp" == key:
                currentstatus.room1_acboost_max_temp = value
            if "room2_acboost_max_temp" == key:
                currentstatus.room2_acboost_max_temp = value

            if "room1_status" == key:
                currentstatus.room1_status = value
            if "room2_status" == key:
                currentstatus.room2_status = value

            if "room1_temperature" == key:
                currentstatus.room1_temperature = value
            if "room2_temperature" == key:
                currentstatus.room2_temperature = value

            if "room1_humidity" == key:
                currentstatus.room1_humidity = value
            if "room2_humidity" == key:
                currentstatus.room2_humidity = value

            if "room1_light" == key:
                currentstatus.room1_light = value
            if "room2_light" == key:
                currentstatus.room2_light = value

            if "room1_ac_speed" == key:
                currentstatus.room1_ac_speed = value
            if "room2_ac_speed" == key:
                currentstatus.room2_ac_speed = value

            if "room1_target_temperature" == key:
                currentstatus.room1_target_temperature = value
            if "room2_target_temperature" == key:
                currentstatus.room2_target_temperature = value

            if "room1_target_humidity" == key:
                currentstatus.room1_target_humidity = value
            if "room2_target_humidity" == key:
                currentstatus.room2_target_humidity = value

            if "room1_lights_on_time" == key:
                currentstatus.room1_lights_on_time = value
            if "room2_lights_on_time" == key:
                currentstatus.room2_lights_on_time = value

            if "room1_lights_off_time" == key:
                currentstatus.room1_lights_off_time = value
            if "room2_lights_off_time" == key:
                currentstatus.room2_lights_off_time = value

            if "THCtrlConnectionLost" == key:
                currentstatus.alert_THCtrlConnectionLost = value

            if "THS1ConnectionLost" == key:
                currentstatus.alert_THS1ConnectionLost = value

            if "THS2ConnectionLost" == key:
                currentstatus.alert_THS2ConnectionLost = value

            if "THSLConnectionLost" == key:
                currentstatus.alert_THSLConnectionLost = value

            if "room1TempControlFailure" == key:
                currentstatus.alert_room1TempControlFailure = value

            if "room1HumControlFailure" == key:
                currentstatus.alert_room1HumControlFailure = value

            if "room2HumControlFailure" == key:
                currentstatus.alert_room2HumControlFailure = value

            if "room1CoolControlFailure" == key:
                currentstatus.alert_room1CoolControlFailure = value

            if "room2CoolControlFailure" == key:
                currentstatus.alert_room2CoolControlFailure = value

            if "room1_lightmode" == key:
                currentstatus.room1_light_mode = value

            if "room2_lightmode" == key:
                currentstatus.room2_light_mode = value

            if "room1TempCtrlStatus" == key:
                currentstatus.room1_temp_ctrl_status = value

            if "room1HumCtrlStatus" == key:
                currentstatus.room1_hum_ctrl_status = value

            if "room2TempCtrlStatus" == key:
                currentstatus.room2_temp_ctrl_status = value

            if "room2HumCtrlStatus" == key:
                currentstatus.room2_hum_ctrl_status = value

            if "room1_ac_inlet" == key:
                currentstatus.room1_ac_inlet = value

            if "room2_ac_inlet" == key:
                currentstatus.room2_ac_inlet = value

            if "room1_humidification_on_time" == key:
                currentstatus.room1_humidification_on_time = int(value)

            if "room2_humidification_on_time" == key:
                currentstatus.room2_humidification_on_time = int(value)

            if "room1_humidification_off_time" == key:
                currentstatus.room1_humidification_off_time = int(value)

            if "room2_humidification_off_time" == key:
                currentstatus.room2_humidification_off_time = int(value)

        self.write("response handled")

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/logout", LogoutHandler),
    (r"/cgi-bin/tehuco-cgi", CgiHandler),
    (r"/report", ReportHandler),
    (r"/report/", ReportHandler),
    (r"/request", RequestHandler),
    (r"/request/", RequestHandler),
    (r"/response", ResponseHandler),
    (r"/response/", ResponseHandler),
    (r"/js/(.*)",tornado.web.StaticFileHandler, {"path": "./js"}),
    (r"/(.*)",tornado.web.StaticFileHandler, {"path": "./"}),
    (r"/html/(.*)",tornado.web.StaticFileHandler, {"path": "./html"}),
    (r"/images/(.*)",tornado.web.StaticFileHandler, {"path": "./images"}),
    (r"/styles/(.*)",tornado.web.StaticFileHandler, {"path": "./styles"}),
], cookie_secret="06d35553-3331-4569-b419-8748d22bb597")



if __name__ == "__main__":
    application.listen(settings.http_port)
    
#    http_server = tornado.httpserver.HTTPServer(application, ssl_options={
#        "certfile": "server.crt",
#        "keyfile": "server.key",
#    })
#    http_server.listen(settings.https_port)
    tornado.ioloop.IOLoop.instance().start()
    
#    tornado.ioloop.IOLoop.instance().start()
