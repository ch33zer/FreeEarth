print('begin')
"""Example map generator: Outdoor

This script demonstrates vmflib by generating a map with a 2D skybox and
some terrain (a displacement map).

"""

def debug(message):
    if True:
        print(message)

debug('starting imports')

from vmf import *
from vmf.types import Vertex
from vmf.tools import Block
from vmf.brush import DispInfo
from bs4 import BeautifulSoup
import vmf.games.source as source
import requests
import random
import math
import uuid
import os

debug('finished import')

STEPS = 9

FAST = False

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

def gettempfilename(prefix='temp', extension=''): #Random enough
    return os.path.join('.', prefix, str(uuid.uuid1())+extension)

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
    heights = requests.get(query)
    return heights.json()['elevationProfile']

def chunk(l, n):
    return [l[i:i+n] for i in range(0, len(l), n)]

def getbuildingdata(lat1, lon1, lat2, lon2):
    debug('starting download')
    query = "http://api.openstreetmap.org/api/0.6/map?bbox="+(",".join([str(min(lon1, lon2)), str(min(lat1, lat2)), str(max(lon1, lon2)), str(max(lat1, lat2))]))
    print(query)
    r = requests.get(query)
    debug('finished download')
    if r.status_code == 200:
        bldgs = []
        debug('start open')
        soup = BeautifulSoup(r.text)
        debug('finish open')
        osm = soup.osm
        debug('finding way')
        tags = osm.find_all(lambda tag: tag.name=='way' and len(tag.find_all(name='tag', k='building'))==1)
        debug('making refs')
        refs = [[y['ref'] for y in x.find_all('nd')] for x in tags]
        debug('starting lat lon lookup')
        for i in range(len(refs)):
            verts = []
            for j in range(len(refs[i])):
                element=osm.find(name='node', id=refs[i][j])
                verts.append((float(element['lat']), float(element['lon'])))
            bldgs.append(verts)
            debug('finished building')
        debug('finished buildings')
        debug(bldgs)
        del(r)
        del(soup)
        del(osm)
        del(tags)
        del(refs)
        return bldgs
    else: 
        del(r)
        return []

def scalecoords(latlon, latmin, latmax, lonmin, lonmax, worldsize):
    lat = latlon[0]
    lon = latlon[1]
    latran = latmax-latmin
    lonran = lonmax-lonmin
    return (((lat-latmin)/(latran)-.5)*worldsize, ((lon-lonmin)/(lonran)-.5)*worldsize)

def makemap(lat1, lon1, lat2, lon2, aslib=True, game='gm', trippymode = False):
    bounds = getbounds(lat1,lon1,lat2, lon2)
    dist = distancebetweenpoints((lat1,lon1),(lat2,lon2))
    sidelenft = 200
    sidelenunits = convertunits(sidelenft)
    maxterrainheight = 20
    skyheight = convertunits(60)
    maxterrainheightconverted = convertunits(maxterrainheight)
    width = length = convertunits(min(dist, sidelenft))

    wallheight = convertunits(20)

    m = vmf.ValveMap()

    # Environment and lighting
    # Sun angle	S Pitch	Brightness		Ambience
    # 0 225 0	 -25	 254 242 160 400	172 196 204 80
    m.world.skyname = 'sky_day02_01'
    light = source.LightEnvironment()
    light.set_all("0 225 0", -25, "254 242 160 400", "172 196 204 80")

    # Floor
    floor = Block(Vertex(0, 0, -129), (width, length, 64), 'nature/dirtfloor003a')
    floor.top().lightmapscale = 32

    # Displacement map for the floor
    # do cool stuff
    highest = -100000 #Lowest is -32768
    lowest = 10000000 # Taller than everest
    heights = getheightmap(lat1, lon1, lat2, lon2)
    if not FAST and heights:
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
    else:
        debug("FAILED TO GET DISPLACEMENT")
    #Buildings
    if not FAST:
        bldgs = getbuildingdata(lat1,lon1,lat2,lon2)
        if bldgs:
            latmin = lonmin = 190
            latmax = lonmax = -190 #OOB for coords
            for i in range(len(bldgs)):
                for j in range(len(bldgs[i])):
                    lat = bldgs[i][j][0]
                    lon = bldgs[i][j][1]
                    latmin = min(latmin, lat)
                    lonmin = min(lonmin, lon)
                    latmax = max(latmax, lat)
                    lonmax = max(lonmax, lon)
            scaledcoords = [[scalecoords(y, latmin, latmax, lonmin, lonmax, width) for y in x] for x in bldgs]
            for i in range(len(scaledcoords)):
                vertices = scaledcoords[i]
                winners = [random.choice(vertices) for x in range(random.randint(0, len(vertices)))]
                for winner in winners:
                    block = Block(Vertex(winner[0], winner[1], lowest), (random.randint(114, 395), random.randint(56, 440), random.randint(200, wallheight)))
                    if trippymode:
                        block.set_material('wood/mythickwoodyasdf') #trip the fuck out on dongs
                    else:
                        block.set_material('wood/woodwall009a')
                    m.world.children.append(block)
                # first = True
                # x = y = lastx = lasty = firstx = firsty = 0
                # start = Block(Vertex(x1, x2, lowest), (10, 10, wallheight))
                # mid = Block(Vertex((x1+x2)/2,(y1+y2)/2, lowest), (10,10,wallheight))
                # material = 'wood/woodwall009a'
                # return [start, mid]
        else:
            debug("FAILED TO DO BUILDINGS")

    # Ceiling
    ceiling = Block(Vertex(0, 0, skyheight), (sidelenunits, sidelenunits, 64))
    ceiling.set_material('tools/toolsskybox2d')

    # Prepare some upper walls for the skybox
    skywalls = []
    # Left upper wall
    skywalls.append(Block(Vertex(0, (-width/2)-64, 128), (length, 64,  skyheight)))
    # Right upper wall
    skywalls.append(Block(Vertex(0,(width/2)+64, 128), (length, 64, skyheight)))
    # Forward upper wall
    skywalls.append(Block(Vertex( (length/2)+64,0,  128), (64,width,  skyheight)))
    # Rear upper wall
    skywalls.append(Block(Vertex(-(length/2)-64,0,  128), (64,width,  skyheight)))
    for wall in skywalls:
        wall.set_material('tools/toolsskybox2d')
        #wall.set_material('brick/brickwall003a')


    # # Prepare some lower walls to be basic walls
    # walls = []
    # # Left wall
    # walls.append(Block(Vertex(-1024, 0, -384), (64, 2048+64, 256)))
    # # Right wall
    # walls.append(Block(Vertex(1024, 0, -384), (64, 2048+64, 256)))
    # # Forward wall
    # walls.append(Block(Vertex(0, 1024, -384), (2048+64, 64, 256)))
    # # Rear wall
    # walls.append(Block(Vertex(0, -1024, -384), (2048+64, 64, 256)))
    # # Set each wall's material
    # for wall in walls:
    #     wall.set_material('brick/brickwall003a')

    # # Add everything we prepared to the world geometry
    # m.world.children.extend(walls)
    m.world.children.extend(skywalls)
    m.world.children.extend([floor, ceiling])

    # TODO: Define a playerspawn entity

    filename = gettempfilename('data', '.vmf')
    # Write the map to a file
    m.write_vmf(filename)

    options = ""
    if aslib:
        options = "--no-install --no-run "
    os.system("python vmflib/tools/buildbsp.py -g "+ game + " " + options + filename)

    return os.path.splitext(filename)[0]+'.bsp'

if __name__ == '__main__':
    #print(getheightmap(39.275321,-76.654358,39.276,-76.655))
    makemap(39.275321,-76.654358,39.289372,-76.624489, False)
    #res=getbuildingdata(39.275321,-76.654358,39.289372,-76.624489)
    #print(res)
