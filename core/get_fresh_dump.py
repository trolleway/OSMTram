#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging
import argparse
import shutil

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='Download PBF file from web, update it by hourly dump with poly file',
            formatter_class=PrettyFormatter)
    parser.add_argument('--url', dest='dump_url', required=True, help='url of pbf file')
    parser.add_argument('--output', dest='work_dump', required=True, help='path to new pbf file')
    #parser.add_argument('--bbox', dest='bbox', required=False)
    parser.add_argument('--poly', dest='poly', required=False)
    parser.add_argument('--bbox', dest='bbox', required=False)
    parser.add_argument('--mode', dest='mode', required=False,choices=['minute', 'hour', 'day'], default='hour')
    parser.add_argument('--prune',dest='prune', required=False, action='store_true', help='Clear temporary folder')
    parser.add_argument('--skip-osmupdate',dest='skip-osmupdate', required=False, action='store_true')

    parser.epilog = \
        '''Samples:
%(prog)s --project "/home/trolleway/tmp/tests/basemap.qgs" --url "http://download.geofabrik.de/russia/northwestern-fed-district-latest.osm.pbf" --output "../../tests/touchdown/rus-nw.osm.pbf"

''' \
        % {'prog': parser.prog}
    return parser

def get_filename_from_url(dump_url):
    return os.path.basename(dump_url)

def get_folder_from_path(path):
    return os.path.dirname((os.path.abspath(path)))

def get_fresh_dump(dump_url,
work_dump='touchdown/rus-nw.osm.pbf',
bbox='31.0467,58.421,31.4765,58.6117',
poly='poly.poly',
prune=None,
mode='hour',
skip_osmupdate=None):
    #get fresh dump by osmupdate or download from dump

    downloaded_dump=get_filename_from_url(dump_url)
    logger.info('downloaded_dump='+downloaded_dump)
    directory=get_folder_from_path(work_dump)
    logger.info('directory='+directory)
    logger.info('work_dump='+work_dump)
    logger.info('existing of dump='+str(os.path.exists(work_dump)))
    logger.info('prune='+str(prune))
    logger.info('skip_osmupdate='+str(skip_osmupdate))
    updated_dump=os.path.join(directory,'just_updated_dump.osm.pbf')
    temp_dump=os.path.join(directory,'temp_dump.osm.pbf')

    if not os.path.exists(directory):
        os.makedirs(directory)
    if prune == True:
        try:
           shutil.rmtree(directory)
        except:
           logger.error('Error while deleting directory')
           quit()
        os.makedirs(directory)

    #shutil.copyfile(
    #frist run of program
    #download pbf
    if os.path.exists(work_dump) == False:
        cmd = 'aria2c --dir="{dir}" --out="{file}" {dump_url}'
        cmd = cmd.format(dir=directory,file=os.path.basename(work_dump), dump_url=dump_url)
        os.system(cmd)
        #os.rename(downloaded_dump, work_dump) #os.rename should move file beetwen dirs too

    #if prevdump dump exists - run osmupdate, it updating it to last hour state and save as currentdump
    osmupdate_tempdir = os.path.join(directory,'osmupdate_temp')
    osmupdate_tempdir = os.path.join(directory)
    if not os.path.exists(osmupdate_tempdir):
        os.makedirs(osmupdate_tempdir)

    if skip_osmupdate != True:
        #--tempfiles={tempdir}
        cmd = 'osmupdate {work_dump} {updated_dump} -b={bbox} --{mode}'
        cmd = cmd.format(work_dump = work_dump, updated_dump = updated_dump, tempdir=osmupdate_tempdir,poly=poly,bbox=bbox,mode=mode)
    else:
        cmd = 'osmconvert {work_dump} -o={updated_dump}'
        cmd = cmd.format(work_dump = work_dump, updated_dump = updated_dump, tempdir=osmupdate_tempdir,poly=poly)
    logger.info(cmd)
    os.system(cmd)

    #if osmupdate not find updates in internet - new file not created, will be used downloaded file
    if os.path.exists(updated_dump) == True:
        #rename currentdump to prevdump
        os.remove(work_dump)
        os.rename(updated_dump, work_dump)

    # filter dump
    os.rename(work_dump, temp_dump)
    filter_dump(temp_dump,work_dump)
    os.remove(temp_dump)
    return 0

def filter_dump(src,dst):
        filter = '''route= railway= highway= natural=water landuse= waterway=riverbank'''
        output_path_1 = os.path.join(os.path.dirname(src),'filtering1')
        output_path_2 = os.path.join(os.path.dirname(src),'filtering2')
        output_path_3 = dst

        cmd = '''
        osmconvert {dump_path} -o={output_path_1}.o5m
        osmfilter {output_path_1}.o5m --keep= --keep="{filter}" --drop="highway=track highway=path highway=footway highway=service landuse=farmland landuse=meadow natural=forest natural=grassland landuse=forest" --out-o5m >{output_path_2}.o5m
        rm -f {output_path_1}.o5m
        osmconvert {output_path_2}.o5m -o={output_path_3}
        rm -f {output_path_2}.o5m
        '''
        cmd = cmd.format(dump_path=src,output_path_1=output_path_1,output_path_2=output_path_2,output_path_3=output_path_3, filter=filter)
        logger.info(cmd)
        os.system(cmd)
        
        
if __name__ == '__main__':
        parser = argparser_prepare()
        args = parser.parse_args()
        get_fresh_dump(args.dump_url,args.work_dump, bbox=args.bbox,prune=args.prune,mode=args.mode)
