#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging

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
    cmd = 'osmupdate {work_dump} {updated_dump} --hour'
    cmd = cmd.format(work_dump = work_dump, updated_dump = updated_dump)
    logger.info(cmd)
    os.system(cmd)

    #if osmupdate not find updates in internet - new file not created, will be used downloaded file
    if os.path.exists(updated_dump) == True:
        #rename currentdump to prevdump
        os.remove(work_dump)
        os.rename(updated_dump, work_dump)

    return 0
