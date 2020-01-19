#!/usr/bin/python
# -*- coding: utf8 -*-

'''
Inputs:
* dump url
* filter string for osmfilter
* red_zone.geojson(optionaly)
* database creds
* output folder

Returns:
* folder/terminals.geojson
* folder/rotes_with_refs.geojson
'''

import os
import argparse
import logging
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Start convert pbf to basemap layers')
# move all magic variables to up

'''
Usage

python3 /home/trolleway/tmp/OSMTram/core/process_basemap.py --dump_path /home/trolleway/tmp/tests/northwestern-fed-district-latest.osm.pbf --bbox 31.0467,58.421,31.4765,58.6117 --output "/home/trolleway/tmp/tests/"

    osmconvert /home/trolleway/tmp/tests/northwestern-fed-district-latest.osm.pbf -o=/home/trolleway/tmp/tests/tmp1.o5m
    osmfilter /home/trolleway/tmp/tests/tmp1.o5m --keep-tags="all highway= railway= landuse= natural= " --drop-tags="=footway" -o=/home/trolleway/tmp/tests/tmp2.o5m
    osmconvert /home/trolleway/tmp/tests/tmp2.o5m -o=/home/trolleway/tmp/tests/filtered_dump.pbf

    rm -r /home/trolleway/tmp/tests/tmp1.o5m
    rm -r /home/trolleway/tmp/tests/tmp2.o5m

'''


def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('--dump_path', dest='dump_path', required=True, help='Path to local .pbf file. Can both be filtered, or unfiltered')
    parser.add_argument('--bbox', dest='bbox', required=False, help='text bbox')
    parser.add_argument('--output',dest='output', required=True, help='Output folder')

    parser.epilog = \
        '''Samples:
%(prog)s --dump_path country.pbf --output "temp/yaroslavl"

''' \
        % {'prog': parser.prog}
    return parser

def filter_osm_dump(dump_path, folder, bbox=None):
    import json
    import pprint
    pp=pprint.PrettyPrinter(indent=2)

    refs=[]
    output_path_1 = os.path.join(folder,'tmp1')
    output_path_2 = os.path.join(folder,'tmp2')
    output_path_final = os.path.join(folder,FILTERED_DUMP_NAME)
    bbox_string = ''
    if bbox is not None: bbox_string='-b='+bbox

    cmd='''
    osmconvert {dump_path} {bbox_string} -o={output_path_1}.o5m
    osmfilter {output_path_1}.o5m --keep-tags="all highway= railway= landuse= natural= " --drop-tags="=footway" -o={output_path_2}.o5m
    osmconvert {output_path_2}.o5m -o={output_path_final}

    rm -r {output_path_1}.o5m
    rm -r {output_path_2}.o5m

'''
    cmd = cmd.format(dump_path = dump_path,
    filter = filter,
    output_path_1 = output_path_1,
    output_path_2 = output_path_2,
    output_path_final = output_path_final,
    bbox_string = bbox_string)

    logger.debug(cmd)
    os.system(cmd)
    logger.info('pbf filtering complete')



def pbf2layer(dump_path, folder, name='landuse',pbf_layer='multipolygons',where=None,select=None):
    output_file_path = os.path.join(folder,name)+'.gpkg'

    where_string = ''
    if where is not None: where_string = ' -where "{where}"'.format(where=where)
    select_string = ''
    if select is not None: select_string = ' -select "{select}"'.format(select=select)
    cmd = '''
rm -f  {output_file_path}
ogr2ogr -f "GPKG" -overwrite -oo CONFIG_FILE={script_folder}/osmconf_basemap.ini {select_string} {where_string}  {output_file_path} {dump_path} {pbf_layer}
    '''
    cmd = cmd.format(output_file_path = output_file_path,
    dump_path = dump_path,
    pbf_layer = pbf_layer,
    where_string = where_string,
    select_string = select_string,
    script_folder = os.path.dirname(os.path.realpath(__file__)),
    )
    logger.debug(cmd)
    os.system(cmd)

    return 0




def postgis2geojson(host,dbname,user,password,table, folder=''):
    file_path = os.path.join(folder,table) + '.geojson'
    if os.path.exists(file_path):
        os.remove(file_path)

    cmd='''
ogr2ogr -f GeoJSON {file_path}    \
  "PG:host='''+host+''' dbname='''+dbname+''' user='''+user+''' password='''+password+'''" "'''+table+'''"
    '''
    cmd = cmd.format(file_path = file_path)
    print(cmd)
    os.system(cmd)

if __name__ == '__main__':


        FILTERED_DUMP_NAME = 'filtered_dump.pbf'
        parser = argparser_prepare()
        args = parser.parse_args()


        #filter_osm_dump(dump_path=args.dump_path, folder=args.output, bbox = args.bbox)
        pbf2layer(dump_path=os.path.join(args.output,FILTERED_DUMP_NAME),
        folder=args.output,
        pbf_layer='multipolygons',
        name='landuse',
        where="landuse is not null and landuse NOT IN ('grass','meadow','farmland')",
        select="landuse,name"
        )
        pbf2layer(dump_path=os.path.join(args.output,FILTERED_DUMP_NAME),
        folder=args.output,
        pbf_layer='multipolygons',
        name='water',
        where="natural='water' OR waterway='riverbank'",
        select="natural,name,waterway"
        )
        pbf2layer(dump_path=os.path.join(args.output,FILTERED_DUMP_NAME),
        folder=args.output,
        pbf_layer='lines',
        name='highway',
        where="highway is not null and highway NOT IN ('footway','path','track','service')",
        select="highway,name,bridge,tunnel"
        )

        pbf2layer(dump_path=os.path.join(args.output,FILTERED_DUMP_NAME),
        folder=args.output,
        name='railway',
        pbf_layer='lines',
        where="railway is not null and railway NOT IN ('construction','proposed','razed','abandoned','disused')",
        select="railway,name,bridge,tunnel"
        )
