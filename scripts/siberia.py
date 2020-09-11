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



poly='russia.poly'
dump_url = 'http://download.geofabrik.de/russia-latest.osm.pbf'
dump_url = 'http://download.geofabrik.de/russia/crimean-fed-district-latest.osm.pbf'

parser = argparser_prepare()
args = parser.parse_args()

WORKDIR=args.WORKDIR


logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Start')

processor = Processor()

processor.process_sheets('russia.geojson',WORKDIR,dump_name='russia')
quit()
