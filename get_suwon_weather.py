#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- encoding:utf-8-*-
from optparse import OptionParser
import sys, os
from time import gmtime, strftime
import datetime

import urllib2
import json
#import urllib
#import codecs
import time


def read_url(url):
    response = ''
    max_try = 5

    for i in range(max_try, 0, -1):
        try:
            req = urllib2.Request(url)
            response = urllib2.urlopen(req, None, 10).read()
            break
        except Exception as e:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
            time.sleep(max_try - i)

    return response


MYKEY = '''%2BdwihdQ38m4yNh9Zo237RZ3AKJe8DT%2FG7iBzzIMzkP540dw%2F%2FY2jndmdgy2Np4zx3IGvFHo5n7gJFuudMBUvNw%3D%3D'''
def getSuwonCurrentWeather():
    url = '''http://newsky2.kma.go.kr/service/GroundInfoService/CurrentWeather?stnId=119&pageNo=1&numOfRows=1&ServiceKey=%s&_type=json''' % (MYKEY)
    #response = read_url(url)
    rlt = json.loads(read_url(url))
    cdata = {}
    #print rlt.get('response')
    if rlt.get('response') :
        #print rlt['response'].get('body')
        if rlt['response'].get('body'):
            #print rlt['response']['body'].get('items')
            for item in rlt['response']['body']['items']:
                for param in rlt['response']['body']['items'][item]:
                    #print param, rlt['response']['body']['items'][item][param]
                    cdata[param] = rlt['response']['body']['items'][item][param]
    #print cdata
    return cdata

import MySQLdb
DATABASE_HOST = "130.31.132.147"
DATABASE_USER = "root"
DATABASE_NAME = "new_db"
DATABASE_PASSWD = "[password]"

def commitDB_tgif_temphum(site, tempc, hump, timestamp):
    conn = MySQLdb.connect (host = DATABASE_HOST,user = DATABASE_USER,db = DATABASE_NAME,passwd = DATABASE_PASSWD)
    cursor = conn.cursor ()
    cursor.execute ("SELECT VERSION()")
    row = cursor.fetchone ()
    print "server version:", row[0]
    try:
        str_insert = "insert into TEMPHUM (TEMPERATURE, HUMIDITY, MEASURETIME, MEASURESITE) "\
                 "values ('%f','%f','%s','%s')" \
                  % (tempc, hump, timestamp, site)
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        print "Temp: %s C  Humidity: %s %%" % (tempc, hump)
    #print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format( s.temperature(), s.humidity() ),
    print 'insert (%s)' % (str_insert)
    cursor.execute ( str_insert )
    conn.commit()
    cursor.close ()
    conn.close ()

def commitDB_tgif_temphumrain(site, tempc, hump, rain, timestamp, rn15m):
    conn = MySQLdb.connect (host = DATABASE_HOST,user = DATABASE_USER,db = DATABASE_NAME,passwd = DATABASE_PASSWD)
    cursor = conn.cursor ()
    cursor.execute ("SELECT VERSION()")
    row = cursor.fetchone ()
    print "server version:", row[0]
    try:
        str_insert = "insert into TEMPHUMRAIN (TEMPERATURE, HUMIDITY, RAIN, MEASURETIME, MEASURESITE, RAIN15M ) "\
                 "values ('%f','%f','%s','%s','%s', '%s')" \
                  % (tempc, hump, rain, timestamp, site, rn15m)
    except Exception as e:
        print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
        print "Temp: %s C  Humidity: %s %% Rain:%s " % (tempc, hump, rain)
    #print 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format( s.temperature(), s.humidity() ),
    print 'insert (%s)' % (str_insert)
    cursor.execute ( str_insert )
    conn.commit()
    cursor.close ()
    conn.close ()

def getSuwonAWSWeather(minutes):
    measuretime = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
    gettm = measuretime.strftime("%Y%m%d%H%M")
    url = '''http://newsky2.kma.go.kr/iros/RetrieveAwsService2/getOneAwsList?awsId=119&awsDt=%s&ServiceKey=%s&_type=json''' % ( gettm, MYKEY)
    print url
    rlt = json.loads(read_url(url))
    cdata = {}
    if rlt.get('Response') and rlt['Response'].get('Body') and rlt['Response']['Body'].get('MinuteModel'):
        MinuteModel = rlt['Response']['Body']['MinuteModel']
        print ' Okay MinuteModel!', MinuteModel
        if MinuteModel.get('ta'):
            cdata['temperature'] = float(MinuteModel['ta'])
        if MinuteModel.get('hm'):
            cdata['humidity'] = float(MinuteModel['hm'])
        if MinuteModel.get('rnYn'):
            cdata['rain'] = MinuteModel['rnYn']
        if MinuteModel.get('rn15M'):
            cdata['rn15M'] = MinuteModel['rn15M']
    if cdata.get('temperature') and cdata.get('humidity'):
        commitDB_tgif_temphum( 'Suwon-AWS', cdata['temperature'], cdata['humidity'], measuretime.strftime("%Y-%m-%d %H:%M:00") )
        commitDB_tgif_temphumrain( 'Suwon-AWS', cdata['temperature'], cdata['humidity'], cdata['rain'], measuretime.strftime("%Y-%m-%d %H:%M:00") , cdata['rn15M'])
    else:
        print ' can not get data' , rlt, cdata

if __name__ == '__main__' : 
    parser = OptionParser()
    
    parser.add_option("--url", dest="url",
                      help="check url",
                      type='string',
                      default='')
                                        
    (options, args) = parser.parse_args()

    getSuwonAWSWeather(5)
    
    
    #olddata = getSuwonCurrentWeather()
    while 0:
        # compare curdata temparture , tm
        curdata = getSuwonCurrentWeather()
        if curdata.get('tm') and olddata.get('tm') and curdata['tm'] != olddata['tm'] and curdata.get('temperature') :
            print 'tm updated %s to %s' % ( olddata['tm'], curdata['tm'] )
            print olddata , curdata
            olddata = curdata
        elif curdata.get('temperature') and olddata.get('temperature') and curdata['temperature'] != olddata['temperature']:
            print 'interesting! tm are same but temperature are different.%s vs %s' % ( olddata['temperature'], curdata['temperature'] )
            print olddata , curdata
            olddata = curdata
        else:
            if curdata.get('temperature'): print "%s%s " % (curdata['temperature'] , unichr(0x2103)) , 
            print datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        '''
{u'cloudAmountMid': 3, u'sealevelPressure': 1005.1, u'temperature': 31, u'tm': 2018080912, u'visibility': 18.63, u'humidity': 70, u'tamax': 32.2, u'windSpeed': 1.8, u'dewPointTemperature': 24.8, u'cloudAmount': 10, u'stnId': 119, u'windDirection': 27, u'tamin': 26.2}
{u'cloudAmountMid': 3, u'sealevelPressure': 1005.1, u'temperature': 31, u'tm': 2018080912, u'visibility': 18.63, u'humidity': 70, u'tamax': 32.2, u'windSpeed': 1.8, u'dewPointTemperature': 24.8, u'cloudAmount': 10, u'stnId': 119, u'windDirection': 27, u'tamin': 26.2}

'''
        time.sleep(60*3)


