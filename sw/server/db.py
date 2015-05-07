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
        cur.execute("DROP TABLE IF EXISTS kaappi")
        cur.execute("""CREATE TABLE IF NOT EXISTS `kaappi` (
                      `id` int(11) NOT NULL AUTO_INCREMENT,
                      `time` int(11) NOT NULL,
                      `temperature` float NOT NULL,
                      `humidity` float NOT NULL,
                      `soil_1` float NOT NULL,
                      `soil_2` float NOT NULL,
                      `heating_time` SMALLINT NOT NULL,
                      `cooling_time` SMALLINT NOT NULL,
                      `watering_time` SMALLINT NOT NULL,
                      `alarms` BIT(32) NOT NULL,
                      PRIMARY KEY (`id`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1 ;""")

    con.close()

def InsertData(room, ts, temperature, humidity, soil_1, soil_2, heating_time, cooling_time, watering_time, alarms):
    con = Connect()
    
    with con:
        cur = con.cursor()
        print "DB:", ts, temperature, humidity,soil_1, soil_2, heating_time, cooling_time, watering_time, alarms
        cur.execute("INSERT INTO kaappi(id, time, temperature, humidity, soil_1, soil_2, heating_time, \
                                         cooling_time, watering_time, alarms) \
                                         VALUES(0 , %i, %f, %f, %f, %f, %i, %i, %i, %i)" % 
                                         (ts, temperature ,humidity, soil_1, soil_2, heating_time, cooling_time, watering_time, alarms))
        con.commit()

    
def GetDataTemperature(amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM kaappi ORDER BY id DESC LIMIT %u" % (amount))
        rows = cur.fetchall()
        idx = 1
        data = "date,temperature\n"
        for row in rows:
            t = datetime.datetime.fromtimestamp(row["time"])
            data += t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["temperature"]) + "\n"

        return data

def GetDataTemperatureRrd(amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM kaappi ORDER BY id ASC LIMIT %u" % (amount))
        rows = cur.fetchall()
        idx = 1
        data = []
        for row in rows:
            rowdata = []
            rowdata.append(row["time"])
            rowdata.append(row["temperature"])
            data.append(rowdata)

        return data

def GetDataHumidity(amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM kaappi ORDER BY id DESC LIMIT %u" % (amount))
        rows = cur.fetchall()
        idx = 1
        data = "date,humidity\n"
        for row in rows:
            t = datetime.datetime.fromtimestamp(row["time"])
            data += t.strftime("%d-%m-%Y %H:%M:%S") + "," + str(row["humidity"]) + "\n"

        return data

def GetDataHumidityRrd(amount):
    con = Connect()
    
    with con:
        cur = con.cursor()

        lastts = "0"
        lastval = "0"
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT * FROM kaappi ORDER BY id ASC LIMIT %u" % (amount))
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

    print options.create
    
    if (options.create):
        CreateDb()

    data = GetDataTemperatureRrd(100)
    print data
#    data = GetDataHumidity(100)
#    print data
    
    
