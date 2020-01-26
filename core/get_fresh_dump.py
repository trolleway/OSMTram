#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging
import argparse

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='Export QGIS map composer layout to png using pyqgis',
            formatter_class=PrettyFormatter)
    parser.add_argument('--url', dest='dump_url', required=True, help='url of pbf file')
    parser.add_argument('--output', dest='work_dump', required=True, help='path to new pbf file')

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

def get_fresh_dump(dump_url,work_dump='touchdown/rus-nw.osm.pbf'):
    #get fresh dump by osmupdate or download from dump

    downloaded_dump=get_filename_from_url(dump_url)
    logger.info('downloaded_dump='+downloaded_dump)
    directory=get_folder_from_path(work_dump)
    logger.info(directory)

    updated_dump=os.path.join(directory,'just_updated_dump.osm.pbf')


    if not os.path.exists(directory):
        os.makedirs(directory)

    #frist run of program
    if os.path.exists(work_dump) == False:
        os.system('aria2c '+dump_url)
        os.rename(downloaded_dump, work_dump) #os.rename should move file beetwen dirs too

    #if prevdump dump exists - run osmupdate, it updating it to last hour state with MosOblast clipping, and save as currentdump
    cmd = 'osmupdate {work_dump} {updated_dump} -v --hour'
    cmd = cmd.format(work_dump = work_dump, updated_dump = updated_dump)
    logger.info(cmd)
    os.system(cmd)

    #if osmupdate not find updates in internet - new file not created, will be used downloaded file
    if os.path.exists(updated_dump) == True:
        #rename currentdump to prevdump
        os.remove(work_dump)
        os.rename(updated_dump, work_dump)

    return 0

if __name__ == '__main__':
        parser = argparser_prepare()
        args = parser.parse_args()
        get_fresh_dump(args.dump_url,args.work_dump)
