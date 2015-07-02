#!/usr/bin/python3
import shapely, string 
from shapely.geometry import Polygon, Point
from lxml import etree
from optparse import OptionParser
import os, urllib, zipfile, sys

XHTML_NAMESPACE = "http://earth.google.com/kml/2.2"
XHTML = "{%s}" % XHTML_NAMESPACE
NSMAP = {None : XHTML_NAMESPACE}

def poly_list(list_string):
  coord_list = []
  for point in list_string.split(" "):
    coords = point.split(",")
    #print "(" + coords[1] + "," + coords[0] + ")"
    coord_list.append((float(coords[1]),float(coords[0]))) # Google KML has order of (Long, Lat), so converting to (Lat, Long)
    #print coord_list
  #print "Coordinate List is " + str(type(coord_list))
  #for tup in coord_list:
  #  print "Coord is " + str(type(tup))
  #Polygon(coord_list)
  return coord_list

def sev_index(cat_type):
  return {
    'General Thunder' : 0,
    'Marginal Risk' : 1,
    'Slight Risk' : 2,
    'Enhanced Risk' : 3,
    'Moderate Risk' : 4,
    'High Risk' : 5
  }.get(cat_type, -1)

def sev_index_str(cat_index):
  return {
    0 : 'General Thunderstorm',
    1 : 'Marginal',
    2 : 'Slight',
    3 : 'Enhanced',
    4 : 'Moderate',
    5 : 'High'
  }.get(cat_index, 'None')

def sev_index_str_short(cat_index):
  return {
    0 : 'TSTM',
    1 : 'MRGL',
    2 : 'SLGT',
    3 : 'ENH',
    4 : 'MDT',
    5 : 'HIGH'
  }.get(cat_index, 'NONE')

def risk_index_str(risk_index):
  return {
    0 : 'Tornado',
    1 : 'Wind',
    2 : 'Hail'
  }.get(risk_index, 'None')

def risk_to_column(name, risk):
  if(risk == 0):
    return { 
      "2 %" : 0,
      "5 %" : 1,
      "10 %" : 2,
      "15 %" : 3,
      "30 %" : 4,
      "45 %" : 5,
      "60 %" : 6,
      "Significant Severe" : 7
    }.get(name, -1)
  else:
    return { 
      "5 %" : 0,
      "15 %" : 1,
      "30 %" : 2,
      "45 %" : 3,
      "60 %" : 4,
      "Significant Severe" : 5
    }.get(name, -1)

def risk_column_to_perc(column, risk):
  if(risk == 0):
    return { 
      0 : "2%",
      1 : "5%",
      2 : "10%",
      3 : "15%",
      4 : "30%",
      5 : "45%",
      6 : "60%",
      7 : "SIG"
    }.get(column, -1)
  else:
    return { 
      0 : "5%",
      1 : "15%",
      2 : "30%",
      3 : "45%",
      4 : "60%",
      5 : "SIG"
    }.get(column, "NONE")

def polygon_parser(poly_elm):
  outer = []
  inner = []
  for child in poly_elm:
    if(child.tag == XHTML + "outerBoundaryIs"):
     outer = poly_list(child.find(".//" + XHTML + "coordinates").text)
    if(child.tag == XHTML + "innerBoundaryIs"):
     inner.append(poly_list(child.find(".//" + XHTML + "coordinates").text))
  #print "inner = " + str(len(inner))
  #print "Outer " + str(outer)
  #for inner_list in inner:
  #  print "Inner: " + str(inner_list)
  return Polygon(outer, inner)

loc = Point(35.181651,-97.440069) #(SPC/NWC office)
parser = etree.XMLParser(ns_clean=True)
cat_list = ("http://www.spc.noaa.gov/products/outlook/day1otlk_cat.kml","http://www.spc.noaa.gov/products/outlook/day2otlk_cat.kml","http://www.spc.noaa.gov/products/outlook/day3otlk_cat.kml")
day1_perc_list = ("http://www.spc.noaa.gov/products/outlook/day1otlk_torn.kml", "http://www.spc.noaa.gov/products/outlook/day1otlk_wind.kml", "http://www.spc.noaa.gov/products/outlook/day1otlk_hail.kml")
day2_perc = "http://www.spc.noaa.gov/products/outlook/day2otlk_prob.kml"
day3_perc = "http://www.spc.noaa.gov/products/outlook/day3otlk_prob.kml"

#creating flags
optParser = OptionParser()
optParser.add_option("-s", "--short", "--conky", dest="short", action="store_true", help="Display shorthand output instead", default=False)
optParser.add_option("-l", "--legacy", dest="legacy", action="store_true", help="Interprets file as pre-2014 change to Risk Areas", default=False)
optParser.add_option("-p", "--point", "--coord", dest="location", metavar="LAT,LONG", help="Specifiy currently location in Latitude & Longitude")
optParser.add_option("-1", "--day1", dest="day1", action="store_true", help="Also include percentage threat risk of day 1", default=False)
optParser.add_option("-2", "--days23", dest="days23", action="store_true", help="Also include percentage threat risk on days 2 and 3", default=False)
(options, args) = optParser.parse_args()

if options.location is not None:
  coords = options.location.split(",")
  loc = Point(float(coords[0]),float(coords[1]));

for day in range(3):
  #day_cat = etree.parse("examples/day1otlk_cat.kml", parser)
  day_cat = etree.parse(cat_list[day], parser)
  legacy = options.legacy #for Interpting older KML (as tests) - didn't have Marginal nor Enhanced
  risk = -1
  root = day_cat.getroot()
  risk_areas = root.findall(".//" + XHTML + "Placemark")
  poly_risk_areas = [[],[],[],[],[],[]]
# 0 -> TimeSpan
# 1 -> name
# 2 -> Style
# 3 -> ExtendedData
# 4 -> Polygon
  for risk_area in risk_areas:
    poly_risk_areas[sev_index(risk_area[1].text)].append(polygon_parser(risk_area[4]))
  for x in range(6):
      for risk_poly in poly_risk_areas[x]:
        #print "Testing in risk area " + sev_index_str(x)
        if(loc.within(risk_poly)):
          risk = x
  if(options.short):
    if(risk == -1):
      print("Day " + str(day+1) + ": NONE")
    else:
      print("Day " + str(day+1) + ": " + sev_index_str_short(risk))
  else:
    if(risk == -1):
      print("Day " + str(day+1) + ": not in risk area")
    else:
      print("Day " + str(day+1) + ": within " + sev_index_str(risk) + " risk area")
if(options.day1):
  day1_risk = False
  for risk_type in range(3):
    #print(risk_index_str(risk_type))
    risk_xml = etree.parse(day1_perc_list[risk_type], parser)
    perc_for_area = 0
    sig_risk = ""
    if(risk_type == 0): 
      all_risk = 7
      poly_risk_perc = [[],[],[],[],[],[],[],[]]
    else:
      all_risk = 5
      poly_risk_perc = [[],[],[],[],[],[]]
    root = risk_xml.getroot()
    risk_areas = root.findall(".//" + XHTML + "Placemark")
    #Check percentage first
    # 0 -> TimeSpan
    # 1 -> visibility
    # 2 -> name
    # 3 -> Style
    # 4 -> ExtendedData
    # 5 -> Polygon
    for perc in risk_areas:
     #print(perc[2].text + " -> " + str(risk_to_column(perc[2].text, risk_type)) + " -> " + str(risk_column_to_perc(risk_to_column(perc[2].text, risk_type),risk_type)))
      poly_risk_perc[risk_to_column(perc[2].text, risk_type)].append(polygon_parser(perc[5]))
      #print(len(poly_risk_perc[risk_to_column(perc[2].text, risk_type)]))
      #print(polygon_parser(perc[5]))
    #print("Done with " + risk_index_str(risk_type))
    for x in range(all_risk):
      #print(str(risk_column_to_perc(x,risk_type)) + " has " + str(len(poly_risk_perc[x])) + " polygons.")
      for perc_poly in poly_risk_perc[x]:
        #print(risk_column_to_perc(x,risk_type))
        if(loc.within(perc_poly)):
          perc_for_area = risk_column_to_perc(x,risk_type)
          day1_risk = True
    for sig_poly in poly_risk_perc[all_risk]:
      if(loc.within(sig_poly)):
        sig_risk = " including a significant severe"
    if(not(perc_for_area == 0)):
      print(perc_for_area + " " + risk_index_str(risk_type) + sig_risk + " risk for your area (Day 1)")
  if(not(day1_risk)):
    print("No specialized risk for area (Day 1)")
if(options.days23):
  for day in range(2,4):
    day_risk = False
    if(day == 2):
     day_xml = etree.parse(day2_perc, parser)
    if(day == 3):
     day_xml = etree.parse(day3_perc, parser)
    perc_for_area = 0
    sig_risk = ""
    poly_risk_perc = [[],[],[],[],[],[]]
    root = day_xml.getroot()
    risk_areas = root.findall(".//" + XHTML + "Placemark")
    for perc in risk_areas:
     #print(perc[2].text + " -> " + str(risk_to_column(perc[2].text, -1)) + " -> " + str(risk_column_to_perc(risk_to_column(perc[2].text, -1),-1)))
      poly_risk_perc[risk_to_column(perc[2].text, -1)].append(polygon_parser(perc[5]))
    for x in range(5):
      #print("Testing " + risk_column_to_perc(x,-1))
      for perc_poly in poly_risk_perc[x]:
        if(loc.within(perc_poly)):
          perc_for_area = risk_column_to_perc(x,-1)
          day_risk = True
        #print(loc.within(perc_poly))
    for sig_poly in poly_risk_perc[5]:
      if(loc.within(sig_poly)):
        sig_risk = " including a significant severe"
    if(not(day_risk)):
      print("No risk for your area (Day " + str(day) + ")")
    else:
      print(perc_for_area + sig_risk + " risk for your area (Day " + str(day) + ")")
#  for child in risk_area:
#    if(child.tag == XHTML + "name"):
#    print child.text + " -> " + str(sev_index(child.text))
#    elif(child.tag == XHTML + "Polygon"):
#    polygon_parser(child)

