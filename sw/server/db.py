#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import datetime
import MySQLdb as mdb
from optparse import OptionParser
import settings

def Connect():
    con = mdb.connect('localhost', settings.dbuser, settings.dbpassword, settings.dbdatabase);
    return con

def CreateDb():
    con = Connect()
    with con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS room1")
        cur.execute("""CREATE TABLE IF NOT EXISTS `room1` (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `time` int(11) NOT NULL,
                      `temperature` float NOT NULL,
                      `humidity` float NOT NULL,
                      `tgt_temperature` float NOT NULL,
                      `tgt_humidity` float NOT NULL,
                      `heating_time` SMALLINT NOT NULL,
                      `cooling_time` SMALLINT NOT NULL,
                      `humidifiying_time` SMALLINT NOT NULL,
                      `lights_on_time` SMALLINT NOT NULL,
                      `alarms` BIT(32) NOT NULL,
                      PRIMARY KEY (`id`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;""")

        cur.execute("DROP TABLE IF EXISTS room2")
        cur.execute("""CREATE TABLE IF NOT EXISTS `room2` (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `time` int(11) NOT NULL,
                      `temperature` float NOT NULL,
                      `humidity` float NOT NULL,
                      `tgt_temperature` float NOT NULL,
                      `tgt_humidity` float NOT NULL,
                      `heating_time` SMALLINT NOT NULL,
                      `cooling_time` SMALLINT NOT NULL,
                      `humidifiying_time` SMALLINT NOT NULL,
                      `lights_on_time` SMALLINT NOT NULL,
                      `alarms` BIT(32) NOT NULL,
                      PRIMARY KEY (`id`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;""")

        cur.execute("DROP TABLE IF EXISTS leak")
        cur.execute("""CREATE TABLE IF NOT EXISTS `leak` (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `time` int(11) NOT NULL,
                      `temperature1` float NOT NULL,
                      `humidity1` float NOT NULL,
                      `temperature2` float NOT NULL,
                      `humidity2` float NOT NULL,
                      `temperature3` float NOT NULL,
                      `humidity3` float NOT NULL,
                      `temperature4` float NOT NULL,
                      `humidity4` float NOT NULL,
                      `temperature5` float NOT NULL,
                      `humidity5` float NOT NULL,
                      PRIMARY KEY (`id`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;""")


        cur.execute("DROP TABLE IF EXISTS currentstatus")
        cur.execute("""CREATE TABLE IF NOT EXISTS `currentstatus` (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `time` int(11) NOT NULL,
                      `r1_temperature` float NOT NULL,
                      `r1_humidity` float NOT NULL,
                      `r1_tgt_temperature` float NOT NULL,
                      `r1_tgt_humidity` float NOT NULL,
                      `r1_lights_on_time` SMALLINT NOT NULL,
                      `r1_lights_off_time` SMALLINT NOT NULL,
                      `r1_ac_in` SMALLINT NOT NULL,
                      `r1_ac_out` SMALLINT NOT NULL,
                      `r2_temperature` float NOT NULL,
                      `r2_humidity` float NOT NULL,
                      `r2_tgt_temperature` float NOT NULL,
                      `r2_tgt_humidity` float NOT NULL,
                      `r2_lights_on_time` SMALLINT NOT NULL,
                      `r2_lights_off_time` SMALLINT NOT NULL,
                      `r2_ac_in` SMALLINT NOT NULL,
                      `r2_ac_out` SMALLINT NOT NULL,
                      `alarms` BIT(32) NOT NULL,
                      PRIMARY KEY (`id`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;""")

    con.close()

def InsertData(room, ts, temperature, humidity, tgt_temperature, tgt_humidity, heating_time, cooling_time, humidifiying_time, lights_on_time, alarms):
    con = Connect()
    
    with con:
        cur = con.cursor()
        cur.execute("INSERT INTO %s(id, time, temperature, humidity, tgt_temperature, tgt_humidity, heating_time, \
                                         cooling_time, humidifiying_time, lights_on_time, alarms) \
                                         VALUES(0 , %i, %f, %f, %f, %f, %i, %i, %i, %i, %i)" % (room, ts, temperature ,humidity, tgt_temperature, tgt_humidity, heating_time, cooling_time, humidifiying_time, lights_on_time, alarms))
        con.commit()

def InsertLeakData(ts, t1, h1, t2, h2, t3, h3, t4, h4, t5, h5):
    con = Connect()
    
    with con:
        cur = con.cursor()
        cur.execute("INSERT INTO leak(id, time, temperature1, humidity1, \
                                                temperature2, humidity2, \
                                                temperature3, humidity3, \
                                                temperature4, humidity4, \
                                                temperature5, humidity5) \
                                         VALUES(0 , %i, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f)" \
                                         % (ts, t1 ,h1, \
                                                t2 ,h2, \
                                                t3, h3, \
                                                t4 ,h4, \
                                                t5 ,h5 ))
        con.commit()

def GetDataLeak(amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM leak ORDER BY id DESC LIMIT %u" % (amount))
        rows = cur.fetchall()
        idx = 1
        
        data = "sensor,date,value\n"
        for row in rows:
            t = datetime.datetime.fromtimestamp(row["time"])
            data += "ANTURI1," + t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["humidity1"]) + "\n"
            data += "ANTURI2," + t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["humidity2"]) + "\n"
            data += "ANTURI3," + t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["humidity3"]) + "\n"
            data += "ANTURI4," + t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["humidity4"]) + "\n"
            data += "ANTURI5," + t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["humidity5"]) + "\n"
        return data

def GetDataLeakForRrd(amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM leak ORDER BY id ASC LIMIT %u" % (amount))
        rows = cur.fetchall()
        idx = 1
        
        data = []
        for row in rows:
            rowdata = []
            rowdata.append(row["time"])
            rowdata.append(row["humidity1"])
            rowdata.append(row["humidity2"])
            rowdata.append(row["humidity3"])
            rowdata.append(row["humidity4"])
            rowdata.append(row["humidity5"])
            data.append(rowdata)
        return data

    
def GetDataTemperature(room, amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM %s ORDER BY id DESC LIMIT %u" % (room, amount))
        rows = cur.fetchall()
        idx = 1
        data = "date,temperature\n"
        for row in rows:
            t = datetime.datetime.fromtimestamp(row["time"])
            data += t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["temperature"]) + "\n"

        return data

def GetDataTemperatureRrd(room, amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM %s ORDER BY id ASC LIMIT %u" % (room, amount))
        rows = cur.fetchall()
        idx = 1
        data = []
        for row in rows:
            rowdata = []
            rowdata.append(row["time"])
            rowdata.append(row["temperature"])
            rowdata.append(row["tgt_temperature"])
            data.append(rowdata)

        return data

def GetDataHumidity(room, amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM %s ORDER BY id DESC LIMIT %u" % (room, amount))
        rows = cur.fetchall()
        idx = 1
        data = "date,humidity\n"
        for row in rows:
            t = datetime.datetime.fromtimestamp(row["time"])
            data += t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["humidity"]) + "\n"

        return data

def GetDataHumidityRrd(room, amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM %s ORDER BY id ASC LIMIT %u" % (room, amount))
        rows = cur.fetchall()
        idx = 1
        data = []
        for row in rows:
            rowdata = []
            rowdata.append(row["time"])
            rowdata.append(row["humidity"])
            rowdata.append(row["tgt_humidity"])
            data.append(rowdata)
        return data


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-c", "--create", dest="create", action="store_true", help="create database")

    (options, args) = parser.parse_args()

    data = GetDataTemperature("room1", 100)
    print data
    data = GetDataHumidity("room1", 100)
    print data
    
    data = GetDataLeak(100)
    print data
    
    print options.create
    
    if (options.create):
        CreateDb()
    
