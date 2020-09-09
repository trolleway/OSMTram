#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging

import sys
import argparse
sys.path.append("../core")
from qgis_project_substitute import substitute_project

from processor import Processor


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



poly='siberia.poly'
dump_url = 'http://download.geofabrik.de/russia/siberian-fed-district-latest.osm.pbf'

parser = argparser_prepare()
args = parser.parse_args()

WORKDIR=args.WORKDIR


logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Start')

processor = Processor()

processor.process_sheets('siberia.geojson',WORKDIR,dump_name='siberia')
quit()

cities = list()
#use http://bboxfinder.com to obtain bbox in EPSG:3857

cities.append({'name':'Красноярск','bbox_map_3857':'10321750.5515,7552322.3612,10357226.8873,7576333.1427'})



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
    processor.process_map(
    name=city['name'],
    WORKDIR=WORKDIR,
    bbox=city['bbox'], 
    layout_extent = city['layout_extent'],
    osmfilter_string='route=tram',
    prune=args.prune,
    dump_url=dump_url,
    poly=poly,
    dump_name='siberia',
    skip_osmupdate=args.skip_osmupdate
    )
    
