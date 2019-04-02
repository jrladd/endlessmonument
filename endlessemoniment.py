#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy, time, sys, re
import datetime as d
# from skyfield import api
from itertools import chain
import pytz as tz
import zipcodes as zc
from secrets import *

# ts = api.load.timescale()
# e = api.load('de421.bsp')

# from skyfield import almanac

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
tapi = tweepy.API(auth)

filename=open("epithalamion.txt", 'r')
f=filename.readlines()
print("I've started")
filename.close()

# Calculate the lines in the day and night section of the poems
def parse_poem_todaynight(lines):
	sunlight_lines=lines[73:298]
	nighttime_lines=lines[0:73]+lines[298:len(lines)+1]
	return sunlight_lines,nighttime_lines

def get_timezone(zipcode, cw, citystate):
	if zipcode==None:
		for t in tz.all_timezones:
			if citystate[0] in t:
				return t
			elif citystate[1] in t:
				return t
	else:
		timezone=cw['condition']['date'].split(' ')[-1]
		for t in tz.all_timezones:
			if timezone in t:
				return t
#A function for replacing standard time notation with the time in minutes.
def rendertime(time):
	if time[-2:]=="am":
		hours=int(time.split(':')[0])
		minutes=int((time.split(':')[1]).split(' ')[0])
		time_in_minutes=60*hours+minutes
		return time_in_minutes
	elif time[-2:]=="pm" and time[:2]!="12":
		hours=int(time.split(':')[0])
		minutes=int((time.split(':')[1]).split(' ')[0])
		time_in_minutes=60*(hours+12)+minutes
		return time_in_minutes
	else:
		hours=int(time.split(':')[0])
		minutes=int((time.split(':')[1]).split(' ')[0])
		time_in_minutes=60*hours+minutes
		return time_in_minutes

# def retrieveline(location):
# 	#Find zipcode for the location
# 	citystate=location.split(", ")
# 	zipcode=zc.findzipcode_withcitystate(citystate[0], citystate[1])
# 	if zipcode==None:
# 		locations=[k for k,v in w.get_location_ids(location).iteritems()]
# 		locationcode=locations[0]
# 	#Calculate the amount of sunlight and darkness for a particular location, as well as the local time for that location.
# 	else:
# 		locations=[k for k,v in w.get_location_ids(zipcode).iteritems()]
# 		locationcode=locations[0]
# 	cw=w.get_weather_from_yahoo(locationcode)
# 	rises=cw['astronomy']['sunrise']
# 	sets=cw['astronomy']['sunset']
#
# 	zone=get_timezone(zipcode, cw, citystate)
# 	zone=tz.timezone(zone)
# 	ct=d.datetime.now(zone)
# 	current_time=ct.hour*60+ct.minute
#
# 	sunrise_time=rendertime(rises)
# 	sunset_time=rendertime(sets)
#
# 	daylight_hours=sunset_time-sunrise_time
# 	nighttime_hours=(sunrise_time+720)-(sunset_time-720)
#
# #Get line if it's daytime
# 	if current_time > sunrise_time and current_time < sunset_time:
# 		line_interval=1-(float(sunset_time-current_time)/daylight_hours)
# 		needed_line=sunlines[int(len(sunlines)*line_interval)]
# 		return needed_line
# # Get line if it's night time
# 	else:
# 		line_interval=1-(float((sunrise_time+720)-current_time)/nighttime_hours)
# 		needed_line=nightlines[int(len(nightlines)*line_interval)]
# 		return needed_line


#Create two different divisions in the poem
#Longlines and Shortlines
shortlines_file=open('shortlines.txt', 'r')
shortlines=shortlines_file.readlines()
shortlines_file.close()

longlines_file=open('longlines.txt', 'r')
longlines= longlines_file.readlines()
longlines_file.close()

#Lines that take place during the day, and ones set at night
poem_daynight=parse_poem_todaynight(f)
sunlines=poem_daynight[0]
nightlines=poem_daynight[1]



def reply_to_tweets():
	our_tweets=tapi.user_timeline(count=5)
	ids=[]
	for tweet in our_tweets:
		ids.append(tweet.id)
	m=tapi.mentions_timeline(max(ids))
	for s in m:
		status=s.text
		tweet_id=s.id_str
		username='@'+s.author.screen_name
		st=status.split()
		location_input=" ".join(st[1:])
		try:
			line_for_tweet=retrieveline(location_input)
			new_reply="%(u)s %(l)s" % {'u': username, 'l': line_for_tweet}
			tapi.update_status(new_reply, tweet_id)
		except AttributeError:
			new_reply="%(u)s No luck with that location, here's the line for St. Louis: %(l)s" % {'u': username, 'l': retrieveline("Saint Louis, MO")}
			tapi.update_status(new_reply, tweet_id)
		except KeyError:
			new_reply="%(u)s No luck with that location, here's the line for St. Louis: %(l)s" % {'u': username, 'l': retrieveline("Saint Louis, MO")}
			tapi.update_status(new_reply, tweet_id)
		except IndexError:
			new_reply="%(u)s No luck with that location, here's the line for St. Louis: %(l)s" % {'u': username, 'l': retrieveline("Saint Louis, MO")}
			tapi.update_status(new_reply, tweet_id)




def get_diurnal(current_time):
	diurnal_day_in_seconds=24*60*60
	poem_time = int(((current_day_from_march-1)*(diurnal_day_in_seconds/365))/60)
	print("Poem Time for Today:", poem_time)
	if poem_time==current_time:
		new_tweet="%s #diurnal" % longlines[current_day_from_march-1]
		tapi.update_status(new_tweet)
		print("Tweeted!")

def get_sidereal(t):
	sidereal_day_in_seconds=23*60*60+56*60+4.0916
	if current_day_from_march < 360 and int(((current_day_from_march-1)*(sidereal_day_in_seconds/360))/60)==int(t/60):
		new_tweet="%s #sidereal" % longlines[current_day_from_march-1]
		tapi.update_status(new_tweet)

def get_shortline(t):
	for line in shortlines:
		if int((((current_day_from_march-1)*236)-900)/60)==int(t/60) and f[f.index(line)+1]==longlines[current_day_from_march-1]:
			tapi.update_status(line)

#
# if (current_time/60) % 2 == 0:
# 	reply_to_tweets()

# latlong = zc.findlatlong_withcitystate("Saint Louis", "MO")
# stl = api.Topos(latlong[0].strip("' \""), latlong[1].strip("' \""))

while True:
	ct=d.datetime.now()
	days_in_a_month=[31,28,31,30,31,30,31,31,30,31,30,31]
	current_day=sum(days_in_a_month[0:ct.month-1])+ct.day
	current_time=ct.hour*60+ct.minute
	print("Day:", current_day)
	print("Time:", current_time)

	start_in_march=list(chain(range(60,366), range(1,60)))
	current_day_from_march = start_in_march.index(current_day+1)
	print("Day if 0 is March 1st:", current_day_from_march)
	get_diurnal(current_time)
	get_sidereal(current_time)
	get_shortline(current_time)
	time.sleep(60)
