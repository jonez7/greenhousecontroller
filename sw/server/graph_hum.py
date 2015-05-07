#!/usr/bin/python

import time
import db
from math import sin, pi
from random import random

from pyrrd.rrd import RRD, RRA, DS
from pyrrd.graph import DEF, CDEF, VDEF
from pyrrd.graph import LINE, AREA, GPRINT
from pyrrd.graph import ColorAttributes, Graph

def GenerateGraph():

    data = db.GetDataTemperatureRrd(10000)
    #print len(data)

    filename = 'humidity.rrd'
    graphfile = 'humidity.png'
    graphfileLg = 'humidity-large.png'

    day = 24 * 60 * 60
    week = 7 * day
    month = day * 30
    quarter = month * 3
    half = 365 * day / 2
    year = 365 * day

    startTime = data[0][0] -1
    endTime   = data[-1][0]
    step = 1000
    maxSteps = int((endTime-startTime)/step)

    # Let's create and RRD file and dump some data in it
    dss = []
    ds1 = DS(dsName='humidity', dsType='GAUGE', heartbeat=60)
    dss.extend([ds1])

    #week: RA:AVERAGE:0.5:6:336
    #For Daily Graph, every 5 minute average for 24 hours:
    #RRA:AVERAGE:0.5:1:288
    rra1 = RRA(cf='AVERAGE', xff=0.5, steps=1, rows=1440)

    #For Weekly Graph, every 30 minute average for 7 days:
    #RRA:AVERAGE:0.5:6:336
    #rra1 = RRA(cf='AVERAGE', xff=0.5, steps=6, rows=336)

    #For Monthly Graph, every 2 hour average for 30 days:
    #RRA:AVERAGE:0.5:24:360
    #rra1 = RRA(cf='AVERAGE', xff=0.5, steps=32, rows=1080)

    #For Yearly Graph, every 1 day average for 365 days:
    #RRA:AVERAGE:0.5:288:365
    #rra1 = RRA(cf='AVERAGE', xff=0.5, steps=96, rows=365)

    rras = []
    #rra1 = RRA(cf='AVERAGE', xff=0.5, steps=24, rows=1460)
    rras.append(rra1)

    myRRD = RRD(filename, ds=dss, rra=rras, start=startTime)
    myRRD.create()

    # let's generate some data...
    currentTime = startTime
    i = 0
    for row in data:
        timestamp = row[0]
        value1 = row[1]

        # lets update the RRD/purge the buffer ever 100 entires
        i = i + 1
        if i % 100 == 0:
            myRRD.update(debug=False)

        # when you pass more than one value to update buffer like this,
        # they get applied to the DSs in the order that the DSs were
        # "defined" or added to the RRD object.
        myRRD.bufferValue(timestamp, value1)
    # add anything remaining in the buffer
    myRRD.update()

    # Let's set up the objects that will be added to the graph
    def1 = DEF(rrdfile=myRRD.filename, vname='anturi1', dsName=ds1.name)
    vdef1 = VDEF(vname='myavg', rpn='%s,AVERAGE' % def1.vname)
    sensor1 = LINE(defObj=def1, color='#4544FC', legend='anturi1')
    line1 = LINE(defObj=vdef1, color='#01FF13', legend='Average', stack=True)

    # Let's configure some custom colors for the graph
    ca = ColorAttributes()
    ca.back = '#000000'
    ca.canvas = '#000000'
    ca.shadea = '#000000'
    ca.shadeb = '#111111'
    ca.mgrid = '#CCCCCC'
    ca.axis = '#FFFFFF'
    ca.frame = '#AAAAAA'
    ca.font = '#FFFFFF'
    ca.arrow = '#FFFFFF'

    # Now that we've got everything set up, let's make a graph
    #startTime = endTime - 3 * month
    g = Graph(graphfile, start=startTime, end=endTime, vertical_label='kosteus', color=ca)
    g.data.extend([def1, vdef1, sensor1])
    g.write()

    g.filename = graphfileLg
    g.width = 690
    g.height = 300
    g.write()

if __name__ == "__main__":
    GenerateGraph()
