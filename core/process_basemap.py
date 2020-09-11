#!/usr/bin/python
# -*- coding: utf8 -*-

'''
Inputs:
* pbf file
* bbox
* output folder

Generate
* Some gpkg files for basemap: landuse,water,highways, etc...
* gpkg with land and oceans polygons (clipped by bbox too)
'''

import os
import argparse
import logging

'''
Usage
python3 /home/trolleway/tmp/OSMTram/core/process_basemap.py --dump_path /home/trolleway/tmp/tests/nw.osm.pbf --bbox 31.0467,58.421,31.4765,58.6117 --output "/home/trolleway/tmp/tests/"
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
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")

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
    osmconvert {dump_path} {bbox_string} --complete-ways  --complex-ways -o={output_path_1}.o5m
    osmfilter {output_path_1}.o5m --keep-tags="all type= highway= railway= landuse= natural= water= waterway= " --drop-tags="=footway" -o={output_path_2}.o5m
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

def bbox2ogr_clipdst(bbox):
    """
    convert "29.9997,59.7816,30.6396,60.1117" to "29.9997 59.7816 30.6396 60.1117"
    """
    clipdst = '{x1} {y1} {x2} {y2}'
    clipdst = clipdst.format(
    x1 = bbox.split(',')[0],
    y1 = bbox.split(',')[1],
    x2 = bbox.split(',')[2],
    y2 = bbox.split(',')[3],
    )
    return clipdst

def download_oceans(folder,bbox):
    URL='https://osmdata.openstreetmap.de/download/simplified-water-polygons-split-3857.zip'
    SOURCEFILE='sea_source.zip'
    export_name='oceans.gpkg'
    export_name='water.gpkg'

    export_filepath = os.path.join(folder,export_name)
    filepath = os.path.join(folder,SOURCEFILE)

    if os.path.exists(filepath) == False:
        cmd = '''aria2c --dir="{dir}" --out="{file}" {dump_url}
        '''
        cmd = cmd.format(dir=folder,
        file=os.path.basename(SOURCEFILE),
        dump_url=URL,
        export_filepath=export_filepath,
        clipdst=bbox2ogr_clipdst(bbox))
        os.system(cmd)

    cmd = '''
    ogr2ogr -overwrite {export_filepath} -t_srs EPSG:4326 -clipdst {clipdst} /vsizip/{dir}/{file}/simplified-water-polygons-split-3857
    '''

    #append oceans to water layer
    cmd = '''
    ogr2ogr -append {export_filepath} -nln multipolygons -t_srs EPSG:4326 -clipdst {clipdst} /vsizip/{dir}/{file}/simplified-water-polygons-split-3857
    '''
    cmd = cmd.format(dir=folder,
    file=os.path.basename(SOURCEFILE),
    dump_url=URL,
    export_filepath=export_filepath,
    clipdst=bbox2ogr_clipdst(bbox))
    print(cmd)
    os.system(cmd)

def download_land(folder,bbox):
    URL='https://osmdata.openstreetmap.de/download/simplified-land-polygons-complete-3857.zip'
    SOURCEFILE='land_source.zip'
    export_name='land.gpkg'

    export_filepath = os.path.join(folder,export_name)
    filepath = os.path.join(folder,SOURCEFILE)

    if os.path.exists(filepath) == False:
        cmd = '''aria2c --dir="{dir}" --out="{file}" {dump_url}
        '''
        cmd = cmd.format(dir=folder,
        file=os.path.basename(SOURCEFILE),
        dump_url=URL,
        export_filepath=export_filepath,
        clipdst=bbox2ogr_clipdst(bbox))
        os.system(cmd)

    cmd = '''
    ogr2ogr -overwrite {export_filepath} -t_srs EPSG:4326 -clipdst {clipdst} /vsizip/{dir}/{file}/simplified-land-polygons-complete-3857
    '''
     # simplified-land-polygons-complete-3857/simplified_land_polygons

    cmd = cmd.format(dir=folder,
    file=os.path.basename(SOURCEFILE),
    dump_url=URL,
    export_filepath=export_filepath,
    clipdst=bbox2ogr_clipdst(bbox))
    print(cmd)
    os.system(cmd)

'''ogrinfo /vsizip/simplified-water-polygons-split-3857.zip/simplified-water-polygons-split-3857

ogr2ogr -overwrite ocean.gpkg -t_srs EPSG:4326 -clipdst 29.9997 59.7816 30.6396 60.1117 /vsizip/simplified-water-polygons-split-3857.zip/simplified-water-polygons-split-3857
'''

if __name__ == '__main__':
        FILTERED_DUMP_NAME = 'basemap.osm.pbf'
        parser = argparser_prepare()
        args = parser.parse_args()

        logging.basicConfig(level=logging.WARNING,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        if args.verbose:
            logging.basicConfig(level=logging.INFO)

        logger.info('Start convert pbf to basemap layers')

        filter_osm_dump(dump_path=args.dump_path, folder=args.output, bbox = args.bbox)
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
        where="natural='water' OR waterway='riverbank' OR water='lake'" ,
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

        download_oceans(folder=args.output, bbox = args.bbox)
        download_land(folder=args.output, bbox = args.bbox)
