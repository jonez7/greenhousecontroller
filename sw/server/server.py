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
#        if not self.current_user:
#            self.redirect("/login")
#            return
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
    def get(self):
        print(self.request.uri)
        ts =  int(self.get_argument("ts", default=None, strip=False))
        temp = self.get_argument("temperature", default=None, strip=False)
        currentstatus.temperature = "%.2f" % float(temp)
        currentstatus.humidity    = "%.2f" % float(self.get_argument("humidity", default=None, strip=False))
        currentstatus.heating     = self.get_argument("heating", default=None, strip=False)
        currentstatus.cooling     = self.get_argument("cooling", default=None, strip=False)
        currentstatus.acc_temperature += float(currentstatus.temperature)
        currentstatus.acc_humidity    += float(currentstatus.humidity)
        currentstatus.acc_heating     += float(currentstatus.heating)
        currentstatus.acc_cooling     += float(currentstatus.cooling)
        currentstatus.acc_counter += 1
        if currentstatus.acc_counter > 12:
            t = float(currentstatus.acc_temperature) / float(currentstatus.acc_counter)
            h = float(currentstatus.acc_humidity) / float(currentstatus.acc_counter)
            he = int(float(currentstatus.acc_heating) / float(currentstatus.acc_counter))
            co = int(float(currentstatus.acc_cooling) / float(currentstatus.acc_counter))
            db.InsertData(0, ts, t, h, 0, 0, he, co, 0, 0)
            currentstatus.acc_temperature = 0.0
            currentstatus.acc_humidity    = 0.0
            currentstatus.acc_heating     = 0.0
            currentstatus.acc_cooling     = 0.0
            currentstatus.acc_counter     = 0
        self.write("ok")

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
