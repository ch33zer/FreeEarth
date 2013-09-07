"""Example map generator: Outdoor

This script demonstrates vmflib by generating a map with a 2D skybox and
some terrain (a displacement map).

"""
from vmf import *
from vmf.types import Vertex
from vmf.tools import Block
from vmf.brush import DispInfo
import vmf.games.source as source
import requests
import math

STEPS = 9

def debug(message):
    if True:
        print(message)
def gettexture(center, zoom):
    background = requests.get('http://maps.googleapis.com/maps/api/staticmap?center='+center+'&zoom='+zoom+'&size=640x640&maptype=satellite&sensor=false&format=png32&scale=2')

def getbounds(lat1, lon1, lat2, lon2):
    latstart = max(lat1, lat2)
    latend = min(lat1, lat2)
    latdelta = (latstart-latend) / STEPS
    lonstart = min(lon1, lon2)
    lonend = max(lon1, lon2)
    londelta = (lonstart - lonend) / STEPS
    return dict(latstart=latstart,latend=latend, latdelta=latdelta, lonstart=lonstart, lonend=lonend, londelta=londelta)

#http://www.platoscave.net/blog/2009/oct/5/calculate-distance-latitude-longitude-python/
def distancebetweenpoints(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 20925524 # feet

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d

def convertunits(feet):
    return feet * 16

def getheightmap(lat1,lon1, lat2, lon2):
    bounds = getbounds(lat1,lon1,lat2, lon2)
    coords = []
    for i in range(STEPS):
        for j in range(STEPS):
            coords.append(str(bounds['latstart']+i*bounds['latdelta']))
            coords.append(str(bounds['lonstart']+j*bounds['londelta']))
    query = 'http://open.mapquestapi.com/elevation/v1/profile?key=Fmjtd%7Cluub2h6t2u%2Cr5%3Do5-9uz0g4&shapeFormat=raw&unit=f&latLngCollection='+",".join(coords)
    print(len(query))
    heights = requests.get(query)
    return heights.json()['elevationProfile']

def chunk(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def makemap(lat1, lon1, lat2, lon2, zoom):

    scale = zoom

    bounds = getbounds(lat1,lon1,lat2, lon2)
    dist = distancebetweenpoints((lat1,lon1),(lat2,lon2))
    sidelenft = 200
    sidelenunnits = convertunits(sidelenft)
    maxterrainheight = 20
    maxterrainheightconverted = convertunits(maxterrainheight)
    width = length = min(dist, sidelenft)

    m = vmf.ValveMap()

    # Environment and lighting
    # Sun angle	S Pitch	Brightness		Ambience
    # 0 225 0	 -25	 254 242 160 400	172 196 204 80
    m.world.skyname = 'sky_day02_01'
    light = source.LightEnvironment()
    light.set_all("0 225 0", -25, "254 242 160 400", "172 196 204 80")

    # Floor
    floor = Block(Vertex(0, 0, -128), (convertunits(width), convertunits(length), 64), 'nature/dirtfloor003a')
    floor.top().lightmapscale = 32

    # Displacement map for the floor
    # do cool stuff
    heights = getheightmap(lat1, lon1, lat2, lon2)
    if True and heights:
        highest = -100000 #Lowest is -32768
        lowest = 10000000 # Taller than everest
        valid = False
        for el in heights:
            if el['height'] == -32768:
                continue
            highest = max(highest, el['height'])
            lowest = min(lowest, el['height'])
            valid = True
        if valid:
            avg = (highest+lowest)/2.0
            norms = []
            for el in heights:
                norms.append(Vertex(0,0, 1))
            norms = chunk(norms, STEPS)
            debug('norms')
            debug(norms)
            dists = []
            for el in heights:
                dists.append(convertunits(maxterrainheight*(el['height'] - lowest)/(highest - lowest)) if el['height'] != -32768 else avg - lowest)
            dists = chunk(dists, STEPS)
            debug('dists')
            debug(dists)
            # for i in range(17):
            #     row = []
            #     for j in range(17):
            #         row.append(Vertex(0, 0, 1))
            #     norms.append(row)
            # for i in range(17):
            #     row = []
            #     for j in range(17):
            #         row.append(((i % 2) + ((j+1) % 2)) * 6) # funky pattern
            #     dists.append(row)
            d = DispInfo(round(math.sqrt(STEPS-1)), norms, dists)
            floor.top().children.append(d)  # Add disp map to the ground




    # Ceiling
    ceiling = Block(Vertex(0, 0, maxterrainheightconverted), (sidelenunnits, sidelenunnits, 64))
    ceiling.set_material('tools/toolsskybox2d')

    # Prepare some upper walls for the skybox
    skywalls = []
    # Left upper wall
    skywalls.append(Block(Vertex(-1024-64, 0, 128), (64, 2048+128, 768)))
    # Right upper wall
    skywalls.append(Block(Vertex(1024+64, 0, 128), (64, 2048+128, 768)))
    # Forward upper wall
    skywalls.append(Block(Vertex(0, 1024+64, 128), (2048+128, 64, 768)))
    # Rear upper wall
    skywalls.append(Block(Vertex(0, -1024-64, 128), (2048+128, 64, 768)))
    for wall in skywalls:
        wall.set_material('tools/toolsskybox2d')

    # Prepare some lower walls to be basic walls
    walls = []
    # Left wall
    walls.append(Block(Vertex(-1024, 0, -384), (64, 2048+64, 256)))
    # Right wall
    walls.append(Block(Vertex(1024, 0, -384), (64, 2048+64, 256)))
    # Forward wall
    walls.append(Block(Vertex(0, 1024, -384), (2048+64, 64, 256)))
    # Rear wall
    walls.append(Block(Vertex(0, -1024, -384), (2048+64, 64, 256)))
    # Set each wall's material
    for wall in walls:
        wall.set_material('brick/brickwall003a')

    # Add everything we prepared to the world geometry
    m.world.children.extend(walls)
    m.world.children.extend(skywalls)
    m.world.children.extend([floor, ceiling])

    # TODO: Define a playerspawn entity

    filename = 'out.vmf'
    # Write the map to a file
    m.write_vmf(filename)

if __name__ == '__main__':
    #print(getheightmap(39.275321,-76.654358,39.276,-76.655))
    makemap(39.275321,-76.654358,39.289372,-76.624489, 3)
