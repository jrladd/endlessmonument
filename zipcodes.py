import csv
with open('/home/jrladd/twitterbots/epithalamibot/zips.csv', 'rb') as csvfile:
	zipreader = csv.reader(csvfile)

def findzipcode_withcitystate(city, state):
	with open('/home/jrladd/twitterbots/epithalamibot/zips.csv', 'rb') as csvfile:
		zipreader = csv.reader(csvfile)
		for row in zipreader:
			if city in row[4] and state in row[1]:
				return row[0]

def findzipcode_withlatlong(latitude, longitude):
	with open('/home/jrladd/twitterbots/epithalamibot/zips.csv', 'rb') as csvfile:
		zipreader = csv.reader(csvfile)
		for row in zipreader:
			if latitude in row[2] and longitude in row[3]:
				return row[0]
