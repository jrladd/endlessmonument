#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy, time, sys, re
import datetime as d
from skyfield import api
from itertools import chain
import pytz as tz
import zipcodes as zc
from secrets import *
from geopy.geocoders import ArcGIS
from timezonefinder import TimezoneFinder

# Load necessary Skyfield files
ts = api.load.timescale()
e = api.load('de421.bsp')

from skyfield import almanac


def get_diurnal(current_time):
	"""
	Given the current time, tweet the appropriate time if the
	diurnal time matches correctly.
	"""
	diurnal_day_in_seconds=24*60*60
	poem_time = int(((current_day_from_march-1)*(diurnal_day_in_seconds/365))/60)
	print("Poem Time for Today:", poem_time)
	if poem_time==current_time:
		new_tweet="%s #diurnal" % longlines[current_day_from_march-1]
		tapi.update_status(new_tweet)
		print("Tweeted!")

def get_sidereal(current_time):
	"""
	Given the current time, tweet the appropriate line if the sidereal
	time matches correctly.
	"""
	sidereal_day_in_seconds=23*60*60+56*60+4.0916
	poem_time = int(((current_day_from_march-1)*(sidereal_day_in_seconds/360))/60)
	if current_day_from_march < 360 and poem_time == current_time:
		new_tweet="%s #sidereal" % longlines[current_day_from_march-1]
		tapi.update_status(new_tweet)

def get_shortline(current_time, full_poem):
	"""
	Given the current time and the full poem, tweet the appropriate
	line if the time matches correctly and the right long line has
	just been tweeted.
	"""
	poem_time = int((((current_day_from_march-1)*236)-900)/60)
	todays_longline = longlines[current_day_from_march-1]
	for line in shortlines:
		preceding_line = full_poem[full_poem.index(line)+1]
		if poem_time == current_time and preceding_line==todays_longline:
			tapi.update_status(line)

def parse_poem_todaynight(lines):
	"""
	Pull out the lines in the poem for the day and night sections.
	"""
	sunlight_lines=lines[73:298]
	nighttime_lines=lines[0:73]+lines[298:len(lines)+1]
	return sunlight_lines,nighttime_lines

def get_day_info(location):
	"""
	Given any location, return information about that day.
	Includes: sunrise, sunset, daylight, darkness, and timezone.
	"""
	geolocator = ArcGIS() # Use ArcGIS for geocoding
	loc = geolocator.geocode(location, timeout=5) # Find location

	# Find timezone based on location
	tf = TimezoneFinder()
	tz_string = tf.timezone_at(lng=loc.longitude, lat=loc.latitude)
	timezone = tz.timezone(tz_string)
	
	# Convert geocode to string format that Skyfield needs
	if loc.latitude < 0:
		lat = "{} S".format(loc.latitude)
	else:
		lat = "{} N".format(loc.latitude)
	if loc.longitude < 0:
		long = "{} W".format(loc.longitude)
	else:
		long = "{} E".format(loc.longitude)


	gps = api.Topos(lat,long) #Encode skyfield location

	# Create a time interval from midnight today to midnight tomorrow
	# Sensitive to timezones
	today = d.datetime.now(timezone)
	today = today.replace(hour=0,minute=0,second=0, microsecond=0)
	tomorrow = today+d.timedelta(days=1)
	t0 = ts.utc(today)
	t1 = ts.utc(tomorrow)

	# Find sunrise and sunset times, convert back to orig timezone
	t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(e, gps))
	t0 = t.astimezone(timezone)[0]
	t1 = t.astimezone(timezone)[1]

	# The earlier time is always sunrise
	if t0 < t1:
		sunrise = t0
		sunset = t1
	else:
		sunrise = t1
		sunset = t0

	# Use timedelta to find daylight and darkness
	daylight = sunset-sunrise
	daylight = daylight.total_seconds()

	if daylight > 0: # Find darkness based on daylight
		darkness = 24*60*60 - daylight
	else: # If UTC made daylight negative, get new daylight and darkness
		darkness = abs(daylight)
		daylight = 24*60*60 + daylight

	return (sunrise, sunset, daylight, darkness, timezone, loc.address)

def retrieveline(location, sunlines, nightlines):
	"""
	Given a location string and the daylight and darkness sections
	of the poem, return a line of the poem that correctly corresponds
	to that location at the current time.
	"""
	# Get all necessary information from that day
	sunrise, sunset, daylight, darkness, timezone, place = get_day_info(location)

	# Get current time in correct timezone
	current_time = d.datetime.now(timezone)

	#Get line if it's daytime
	if current_time > sunrise and current_time < sunset:
		# Interval is a fraction of how much time until sunset
		line_interval=1-((sunset-current_time).total_seconds()/daylight)
		# Use interval to get correct line index
		needed_line=sunlines[int(len(sunlines)*line_interval)]
		return needed_line, place, current_time.time().strftime('%H:%M:%S')
	# Get line if it's night time
	else:
		# Find the upcoming sunrise
		if current_time < sunrise:
			sunrise_tomorrow = sunrise
		else:
			sunrise_tomorrow = sunrise + d.timedelta(days=1)
		# Interval is a fraction of how much time until dawn
		line_interval=1-((sunrise_tomorrow-current_time).total_seconds()/darkness)
		# Use interval to get correct line index
		needed_line=nightlines[int(len(nightlines)*line_interval)]
		return (needed_line, place, current_time.time().strftime('%H:%M:%S'))

def reply_to_tweets(sunlines, nightlines):
	"""
	Given the two sections of the poem, find any mentions
	and reply back with the appropriate line of the poem.
	"""
	if len(ids) > 0: # Check only for mentions that haven't previously been dealt with
		m=tapi.mentions_timeline(max(ids))
	else:
		m = tapi.mentions_timeline()
	for s in m: # For each mention
		tweet_id=s.id
		username=s.author.screen_name
		location_input=s.text
		if not hasattr(s, 'retweeted_status') or not hasattr(s, 'quoted_status'): # Make sure tweet is not a retweet or quote tweet
			line_for_tweet, place, time = retrieveline(location_input, sunlines, nightlines) # Based on the status, get a line and some other information
			new_reply='@{u} Here you go! The line for {place} at {time} is: "{l}"'.format(u=username, place=place, time=time, l=line_for_tweet.strip()) # Construct a tweet with that information
			tapi.update_status(new_reply, tweet_id) # Reply to the original tweet
			ids.append(tweet_id) # Record id for original tweet

if __name__ == "__main__":
	# Open up a Twitter API using secret keys
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
	tapi = tweepy.API(auth)

	# Open the full poem
	filename=open("epithalamion.txt", 'r')
	poem=filename.readlines()
	filename.close()

	#Create two different divisions in the poem
	#Longlines and Shortlines
	shortlines_file=open('shortlines.txt', 'r')
	shortlines=shortlines_file.readlines()
	shortlines_file.close()

	longlines_file=open('longlines.txt', 'r')
	longlines= longlines_file.readlines()
	longlines_file.close()

	#Lines that take place during the day, and ones set at night
	poem_daynight=parse_poem_todaynight(poem)
	sunlines=poem_daynight[0]
	nightlines=poem_daynight[1]

	ids = [1113902410978799618] # Start with a known, older id
	while True:
		ct=d.datetime.now() # What date/time is it right now?
		# current_day=ct.timetuple().tm_yday # How many days has it been since January 1st?
		current_day_from_march = ct.toordinal() - d.date(ct.year, 3, 1).toordinal() + 1 # How many days has it been since March 1st?
		current_time=ct.hour*60+ct.minute # How many minutes has it been since midnight?
		print("Day if year starts on March 1st:", current_day_from_march)
		print("Time:", current_time)

		get_diurnal(current_time) # If it's time for a diurnal line, tweet it.
		get_sidereal(current_time) # If it's time for a sidereal line, tweet it.
		get_shortline(current_time, poem) # If it's time for a short line, go ahead and tweet that too!
		reply_to_tweets(sunlines, nightlines) # If anyone has written, reply to them!
		time.sleep(60) # Wait one minute before doing it all again.
