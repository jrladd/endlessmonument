import csv
with open('zips.csv', 'rb') as csvfile:
	zipreader = csv.reader(csvfile)

def findzipcode_withcitystate(city, state):
	with open('zips.csv', 'rb') as csvfile:
		zipreader = csv.reader(csvfile)
		for row in zipreader:
			if city in row[4] and state in row[1]:
				return row[0]

def findlatlong_withcitystate(city, state):
	with open('zips.csv', 'r') as csvfile:
		zipreader = csv.reader(csvfile)
		for row in zipreader:
			if city in row[4] and state in row[1]:
				return row[2:4]

def findzipcode_withlatlong(latitude, longitude):
	with open('zips.csv', 'rb') as csvfile:
		zipreader = csv.reader(csvfile)
		for row in zipreader:
			if latitude in row[2] and longitude in row[3]:
				return row[0]
