#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging

import sys
import argparse
import json
sys.path.append("../core")
from qgis_project_substitute import substitute_project

from processor import Processor


def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='OSMTram process',
            formatter_class=PrettyFormatter)
    parser.add_argument('metadata', help='metadata.json file')        
    parser.add_argument('--skip-osmupdate',dest='skip_osmupdate', required=False, default=None, action='store_true')
    parser.add_argument('--basemap-caching',dest='basemap_caching', required=False, default=None, action='store_true')
    parser.add_argument('--workdir',dest='WORKDIR', required=True)
    parser.add_argument('--where',dest='attribute_filter', required=False,help = 'attrubute filter for layout geojson')
    parser.add_argument('--osmupdate-mode',
    dest='osmupdate_mode', 
    required=False, 
    default='hour', 
    const='hour', 
    choices=['minute', 'hour', 'day'], nargs = '?',
    help = 'osmupdate mode')
        
    parser.epilog = \
        '''Samples:
%(prog)s
--where="name_int = Vidnoe  --skip-osmupdate
--where "name_int = 'Gdansk'" --osmupdate-mode day
''' \
        % {'prog': parser.prog}
    return parser



dump_url = 'http://download.geofabrik.de/russia-latest.osm.pbf'

parser = argparser_prepare()
args = parser.parse_args()

assert os.path.isfile(args.metadata)

with open(args.metadata, 'r') as f:
    metadata_json=f.read()

# parse file
metadata = json.loads(metadata_json)

dump_url = metadata['dump_url']
WORKDIR=args.WORKDIR

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


processor = Processor()




processor.process_sheets(metadata['layout_geojson'],
WORKDIR,
dump_url = metadata['dump_url'],
dump_name = metadata['dump_name'],
attribute_filter = args.attribute_filter,
osmupdate_mode = args.osmupdate_mode,
skip_osmupdate = args.skip_osmupdate,
basemap_caching = args.basemap_caching
)
