#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2018 Pawel Gasiorowski  
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Author: Pawel Gasiorowski
# Version: 1.0
#

import os
import sys
import datetime
import time
import textwrap
import requests
import argparse
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument("--refresh-rate", default="30", type=int, help='The refresh rate of the board in seconds (default 30')
parser.add_argument("--token", help='The security token provided by National Rail Services (the format is: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)')
parser.add_argument("--origin", default='RDG', help='The starting location of the journey (default RDG)')
parser.add_argument("--destination", default='WAT', help='The destination location of the journey (default WAT)')
parser.add_argument("--rows", default='4', help='The number of rows to be returned from API (default 4)')
parser.add_argument("--add-return", action="store_true", help='Additional table that will show return services at present time')
args = parser.parse_args()

if args.token is None:
    print("The token is not set - please set it with --token parameter")
    sys.exit()

starttime = time.time()
url = "https://lite.realtime.nationalrail.co.uk/OpenLDBWS/ldb11.asmx"
headers = {}
headers['content-type'] = 'text/xml;charset=UTF-8'
#headers['SOAPAction'] = 'http://thalesgroup.com/RTTI/2017-10-01/ldb/GetDepartureBoard'
#headers['Accept-encoding'] = 'gzip, x-gzip, deflate, x-bzip2'

ns = {'lt':'http://thalesgroup.com/RTTI/2012-01-13/ldb/types',
'lt6':'http://thalesgroup.com/RTTI/2017-02-02/ldb/types',
'lt7':'http://thalesgroup.com/RTTI/2017-10-01/ldb/types',
'lt4':'http://thalesgroup.com/RTTI/2015-11-27/ldb/types',
'lt5':'http://thalesgroup.com/RTTI/2016-02-16/ldb/types',
'lt2':'http://thalesgroup.com/RTTI/2014-02-20/ldb/types',
'lt3':'http://thalesgroup.com/RTTI/2015-05-14/ldb/types'}

def getRequestBody(token, rows, origin, destination):
    body = """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" 
			 xmlns:typ="http://thalesgroup.com/RTTI/2013-11-28/Token/types" 
			 xmlns:ldb="http://thalesgroup.com/RTTI/2017-10-01/ldb/">
	  	<soap:Header>
			<typ:AccessToken>
				<typ:TokenValue>""" + token + """</typ:TokenValue>
			</typ:AccessToken>
		</soap:Header>
		<soap:Body>
			<ldb:GetDepBoardWithDetailsRequest>
				<ldb:numRows>""" + rows + """</ldb:numRows>
				<ldb:crs>""" + origin + """</ldb:crs>
				<ldb:filterCrs>""" + destination + """</ldb:filterCrs>
			</ldb:GetDepBoardWithDetailsRequest>
		</soap:Body>
	    </soap:Envelope>"""
    return body

def printTimeTable(origin_name, origin_loc_name, dest_name, time_std, time_etd, platform, cars_num, notes):
    print('{:<35s}{:<35s}{:<30s}{:<15s}{:<12s}{:<10s}{:<10s}{:<20}'.format(
        str(origin_name),
        str(origin_loc_name), 
        str(dest_name),
        str(time_std), 
        str(time_etd),
        str(platform),
        str(cars_num), 
        notes))

def getTimeTable(response, at_time):
    xml = ET.fromstring(response.content)
    print(dash)
    print('{:^167}'.format("MESSAGES FOR THIS ROUTE"))
    print(dash)
    messages = xml.findall('.//lt:message', ns)
    origin_loc_from = xml.find('.//lt4:locationName', ns).text
    origin_crs_from = xml.find('.//lt4:crs', ns).text
    destination_loc = xml.find('.//lt4:filterLocationName', ns).text
    destination_crs = xml.find('.//lt4:filtercrs', ns).text
    for message in messages:
        print('{:<167s}'.format(textwrap.fill(str(message.text), width=167)))
        if len(messages) > 1:
            print('\n')

    print(dash)
    print('{:^167}'.format("LIVE TRAINS UPDATE - " + origin_loc_from + " - " + destination_loc + " AT " + at_time))
    print(dash)
    print('{:<35s}{:<35s}{:<30s}{:<15s}{:<12s}{:<10s}{:<10s}{:<20}'.format("ORIGIN", "FROM", "TO", "DEPARTURE", "ETA", "PLATFORM", "CARS NUM", "NOTES"))
    print(dash)
    destinations = xml.findall('.//lt7:service', ns)
    for service in destinations:
        time_etd = service.findtext('{' + ns['lt4'] + '}etd')
        time_std = service.findtext('{' + ns['lt4'] + '}std')
        cars_num = service.findtext('{' + ns['lt4'] + '}length')
        if cars_num is None:
            cars_num = "N/A"
        platform = service.findtext('{' + ns['lt4'] + '}platform')
        if platform is None:
            platform = "--"

        origin_name = service.find('.//lt5:origin', ns)[0].findtext('{' + ns['lt4'] + '}locationName')
        origin_crs = service.find('.//lt5:origin', ns)[0].findtext('{' + ns['lt4'] + '}crs')
        dest_name = service.find('.//lt5:destination', ns)[0].findtext('{' + ns['lt4'] + '}locationName')
        dest_crs = service.find('.//lt5:destination', ns)[0].findtext('{' + ns['lt4'] + '}crs')
        cancel_reason = service.find('.//lt4:cancelReason', ns)
        if cancel_reason is None:
            cancel_reason = 'N/A'
        else:
            cancel_reason = textwrap.wrap(cancel_reason.text, width=20)
        
        if isinstance(cancel_reason, list):
            printTimeTable(str(origin_name) + " - " + str(origin_crs), 
                           str(origin_loc_from) + " - " + str(origin_crs_from),
                           str(destination_loc) + " - " + str(destination_crs),
                           str(time_std), str(time_etd),
                           str(platform), str(cars_num), 
                           str(cancel_reason[0]))
            for i in range(1, len(cancel_reason)):
                printTimeTable("", "", "", "", "", "", "", str(cancel_reason[i]))
        else:
            printTimeTable(str(origin_name) + " - " + str(origin_crs), 
                           str(origin_loc_from) + " - " + str(origin_crs_from),
                           str(destination_loc) + " - " + str(destination_crs),
                           str(time_std), str(time_etd),
                           str(platform), str(cars_num), 
                           str(cancel_reason))

dash = '-' * 167
while True:
    os.system('clear')
    dt = datetime.datetime.today()
    at_time = "%02u/%02u/%04u %02u:%02u:%02u" % (dt.day, dt.month, dt.year, dt.hour, dt.minute, dt.second)
    response = requests.post(url, data=getRequestBody(args.token, args.rows, args.origin, args.destination), headers=headers)
    #print(response.content)
    getTimeTable(response, at_time)
    if args.add_return:
        response_return = requests.post(url, data=getRequestBody(args.token, args.rows, args.destination, args.origin), headers=headers)
        #print(response_return.content)
        getTimeTable(response_return, at_time)
    time.sleep(args.refresh_rate - ((time.time() - starttime) % args.refresh_rate))


