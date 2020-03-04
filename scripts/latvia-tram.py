#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging

import sys
import argparse
sys.path.append("../core")
from qgis_project_substitute import substitute_project


def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='OSMTram process',
            formatter_class=PrettyFormatter)
    parser.add_argument('--prune',dest='prune', required=False, action='store_true', help='Clear temporary folder')
    parser.add_argument('--skip-osmupdate',dest='skip_osmupdate', required=False, action='store_true')
    parser.add_argument('--workdir',dest='WORKDIR', required=True)

    parser.epilog = \
        '''Samples:
%(prog)s

''' \
        % {'prog': parser.prog}
    return parser



POLY='latvia-tram.poly'
dump_url = 'http://download.geofabrik.de/http://download.geofabrik.de/europe/latvia-latest.osm.pbf'

parser = argparser_prepare()
args = parser.parse_args()

WORKDIR=args.WORKDIR


logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Start')

#перенести в core
def process_map(name,
WORKDIR,
bbox,
layout_extent='<Extent ymax="8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>',
prune=None,
skip_osmupdate=None):


    filename = name+'.png'
    if prune == True:
        isprune = ' --prune '
    else:
        isprune = ''

    if skip_osmupdate == True:
        isskip_osmupdate = ' --skip-osmupdate '
    else:
        isskip_osmupdate = ''



    cmd = 'python3 ../core/get_fresh_dump.py --url "{url}" --output "{WORKDIR}/rus-nw.osm.pbf" --poly "{POLY} {prune} {skip_osmupdate}"'
    cmd = cmd.format(url=dump_url,WORKDIR=WORKDIR,bbox=bbox,POLY=POLY,prune=isprune,skip_osmupdate=isskip_osmupdate)
    os.system(cmd)




    #-------------
    cmd = 'python3 ../core/process_basemap.py --dump_path {WORKDIR}/rus-nw.osm.pbf --bbox {bbox} -v --output "{WORKDIR}/" '
    cmd = cmd.format(WORKDIR=WORKDIR,bbox=bbox)
    os.system(cmd)


    cmd = 'osmconvert "{WORKDIR}/rus-nw.osm.pbf" -b={bbox} -o="{WORKDIR}/current_city.osm.pbf"'
    cmd = cmd.format(WORKDIR=WORKDIR,bbox=bbox)
    os.system(cmd)

    cmd = 'python3 ../core/process_routes.py --dump_path "{WORKDIR}/current_city.osm.pbf" --filter "route=trolleybus" --output "{WORKDIR}/" '
    cmd = cmd.format(WORKDIR=WORKDIR)
    logger.info(cmd)
    os.system(cmd)

    substitute_project(
                    src='../qgis_project_templates/retrowave.qgs.template.qgs',
                    dst = WORKDIR+'/out.qgs',
                    layout_extent=layout_extent)

    cmd = 'python3 ../core/pyqgis_client.py --project "{WORKDIR}/out.qgs" --layout "4000x4000" --output "{png_file}" '
    cmd = cmd.format(WORKDIR=WORKDIR,png_file=os.path.join(os.path.realpath(WORKDIR),filename))
    logger.info(cmd)
    os.system(cmd)

cities = list()
#cities.append({'name':'Kaliningrad','bbox':'20.356018,54.6532,20.61248,54.77497','layout_extent':'''<Extent  xmin="2265291" ymin="7296762" xmax="2294848" ymax="7316479"/>'''})
#use http://bboxfinder.com to obtain bbox in EPSG:3857

cities.append({'name':'Daugavpils tram map','bbox_map_3857':'2948405.4920,7530251.1693,2961208.6943,7542060.6902'})
cities.append({'name':'Liepaja tram map','bbox_map_3857':'2332170,7651040,2347228,7667627'})
cities.append({'name':'Riga tram map','2672085.6348,7740897.2873,2698991.4687,7768562.7142'})


# TODO: move to core
from pyproj import Proj, transform

for i, c in enumerate(cities):
    if 'bbox' not in c:
        inProj = Proj('epsg:3857')
        outProj = Proj('epsg:4326')
        x1 = c['bbox_map_3857'].split(',')[0]
        y1 = c['bbox_map_3857'].split(',')[1]
        xmin,ymin = transform(inProj,outProj,x1,y1)
        x2 = c['bbox_map_3857'].split(',')[2]
        y2 = c['bbox_map_3857'].split(',')[3]
        xmax,ymax = transform(inProj,outProj,x2,y2)



        cities[i]['bbox'] = '''{ymin},{xmin},{ymax},{xmax}'''.format(
        xmin=round(xmin,3),
        ymin=round(ymin,3),
        xmax=round(xmax,3),
        ymax=round(ymax,3),
        )

for i, c in enumerate(cities):
    if 'layout_extent' not in c:
        cities[i]['layout_extent'] = '''<Extent xmin="{xmin}" ymin="{ymin}" xmax="{xmax}" ymax="{ymax}"/>'''.format(
        xmin=c['bbox_map_3857'].split(',')[0],
        ymin=c['bbox_map_3857'].split(',')[1],
        xmax=c['bbox_map_3857'].split(',')[2],
        ymax=c['bbox_map_3857'].split(',')[3],
         )


print(cities)
for city in cities:
    #print(city['name'])
    process_map(name=city['name'],WORKDIR=WORKDIR,bbox=city['bbox'], layout_extent = city['layout_extent'],
    prune=args.prune,skip_osmupdate=args.skip_osmupdate)

