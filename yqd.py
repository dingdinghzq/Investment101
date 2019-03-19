# -*- coding: utf-8 -*-
"""
Created on Thu May 18 22:58:12 2017

@author: c0redumb
"""

# To make print working for Python2/3
from __future__ import print_function

# Use six to import urllib so it is working for Python2/3
from six.moves import urllib
# If you don't want to use six, please comment out the line above
# and use the line below instead (for Python3 only).
#import urllib.request, urllib.parse, urllib.error

import time
import pandas as pd
import datetime as dt
import numpy as np

'''
Starting on May 2017, Yahoo financial has terminated its service on
the well used EOD data download without warning. This is confirmed
by Yahoo employee in forum posts.

Yahoo financial EOD data, however, still works on Yahoo financial pages.
These download links uses a "crumb" for authentication with a cookie "B".
This code is provided to obtain such matching cookie and crumb.
'''

# Build the cookie handler
cookier = urllib.request.HTTPCookieProcessor()
opener = urllib.request.build_opener(cookier)
urllib.request.install_opener(opener)

# Cookie and corresponding crumb
_cookie = None
_crumb = None

# Headers to fake a user agent
_headers={
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11'
}

def _get_cookie_crumb():
	'''
	This function perform a query and extract the matching cookie and crumb.
	'''

	# Perform a Yahoo financial lookup on SP500
	req = urllib.request.Request('https://finance.yahoo.com/quote/^GSPC', headers=_headers)
	f = urllib.request.urlopen(req)
	alines = f.read().decode('utf-8')

	# Extract the crumb from the response
	global _crumb
	cs = alines.find('CrumbStore')
	cr = alines.find('crumb', cs + 10)
	cl = alines.find(':', cr + 5)
	q1 = alines.find('"', cl + 1)
	q2 = alines.find('"', q1 + 1)
	crumb = alines[q1 + 1:q2]
	_crumb = crumb

	# Extract the cookie from cookiejar
	global cookier, _cookie
	for c in cookier.cookiejar:
		if c.domain != '.yahoo.com':
			continue
		if c.name != 'B':
			continue
		_cookie = c.value

	# Print the cookie and crumb
	# print('Cookie:', _cookie)
	# print('Crumb:', _crumb)

# we need to handle date before 1970/1/1	
def get_epoch_time(date, is_end_date = False):
	year = int(date[0:4])
	month = int(date[4:6])
	day = int(date[6:8])
	if is_end_date:
		day = day + 1

	if year < 1970:
		d0 = dt.datetime(1970, 1, 1)
		d = dt.datetime(year, month, day)
		d2 = d0 + (d0 - d)
		return -d2.timestamp()
	else:
		d3 = dt.datetime(year, month, day)
		return d3.timestamp()


def load_yahoo_quote(ticker, begindate, enddate, info = 'quote', format_output = 'list'):
	'''
	This function load the corresponding history/divident/split from Yahoo.
	'''

	# Prepare the parameters and the URL
	tb = get_epoch_time(begindate)
	if enddate == 'today':
		enddate = dt.date.today().strftime('%Y%m%d')

	te = get_epoch_time(enddate, True)

	# Check to make sure that the cookie and crumb has been loaded
	global _cookie, _crumb
	if _cookie == None or _crumb == None:
		_get_cookie_crumb()

	param = dict()
	param['period1'] = int(tb)
	param['period2'] = int(te)
	param['interval'] = '1d'
	if info == 'quote':
		param['events'] = 'history'
	elif info == 'dividend':
		param['events'] = 'div'
	elif info == 'split':
		param['events'] = 'split'
	param['crumb'] = _crumb
	params = urllib.parse.urlencode(param)
	url = 'https://query1.finance.yahoo.com/v7/finance/download/{}?{}'.format(ticker, params)
	#print(url)
	req = urllib.request.Request(url, headers=_headers)

	# Perform the query
	# There is no need to enter the cookie here, as it is automatically handled by opener
	f = urllib.request.urlopen(req)
	alines = f.read().decode('utf-8')
	#print(alines)
	if format_output == 'list':
		return alines.split('\n')

	if format_output == 'dataframe':
		nested_alines = [line.split(',') for line in alines.split('\n')[1:]]
		cols = alines.split('\n')[0].split(',')
		adf = pd.DataFrame.from_records(nested_alines[:-1], columns=cols)
		adf['Date'] = pd.to_datetime(adf['Date'])
		adf['Open'] = adf['Open'].astype(float)
		adf['High'] = adf['High'].astype(float)
		adf['Low'] = adf['Low'].astype(float)
		adf['Close'] = adf['Close'].astype(float)
		adf['Adj Close'] = adf['Adj Close'].astype(float)
		adf['Volume'] = adf['Volume'].astype(np.int64)
		return adf