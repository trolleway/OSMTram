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
import psycopg2
import time
import config
import argparse
import logging

# move all magic variables to up

FILTERED_DUMP_NAME = 'routes.osm.pbf'

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)



def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('--dump_path', dest='dump_path', required=True, help='Path to local .pbf file. Can both be filtered, or unfiltered')
    parser.add_argument('--filter', dest='filter', required=True, help='parameter string to osmfilter. \ ')
    parser.add_argument('--red_zone',dest='red_zone', required=False, help='Path to local GeoJSON file with red zone. Routes intersects with red zone will be deleted.')
    parser.add_argument('--output',dest='output', required=True, help='Output folder')

    parser.epilog = \
        '''Samples:
%(prog)s --dump_path yaroslavl.pbf --filter "--tf accept-relations route=trolleybus" --output "temp/yaroslavl"

''' \
        % {'prog': parser.prog}
    return parser

def filter_osm_dump(dump_path,  folder,filter='route=bus',):
        import json
        import pprint
        pp=pprint.PrettyPrinter(indent=2)

        refs=[]
        output_path_1 = os.path.join(folder,'filtering1')
        output_path_2 = os.path.join(folder,'filtering2')
        output_path_3 = os.path.join(folder,FILTERED_DUMP_NAME)

        cmd = '''
        osmconvert {dump_path} -o={output_path_1}.o5m
        osmfilter {output_path_1}.o5m --keep= --keep-relations="{filter}" --out-o5m >{output_path_2}.o5m
        rm -f {output_path_1}.o5m
        osmconvert {output_path_2}.o5m -o={output_path_3}
        rm -f {output_path_2}.o5m
        '''
        cmd = cmd.format(dump_path=dump_path,output_path_1=output_path_1,output_path_2=output_path_2,output_path_3=output_path_3, filter=filter)
        logger.debug(cmd)
        os.system(cmd)

def cleardb(host,dbname,user,password):
    ConnectionString="dbname=" + dbname + " user="+ user + " host=" + host + " password=" + password

    try:
        conn = psycopg2.connect(ConnectionString)
    except:
        print('Unable to connect to the database')
        print(ConnectionString)
        return 0
    cur = conn.cursor()
    sql ='''
    DROP TABLE  IF EXISTS planet_osm_line         CASCADE;
    DROP TABLE  IF EXISTS planet_osm_nodes         CASCADE;
    DROP TABLE  IF EXISTS planet_osm_point         CASCADE;
    DROP TABLE  IF EXISTS planet_osm_polygon     CASCADE;
    DROP TABLE  IF EXISTS planet_osm_rels         CASCADE;
    DROP TABLE  IF EXISTS planet_osm_roads         CASCADE;
    DROP TABLE  IF EXISTS planet_osm_ways         CASCADE;
    DROP TABLE  IF EXISTS route_line_labels         CASCADE;
    --TRUNCATE TABLE  routes_with_refs         CASCADE;
    DROP TABLE  IF EXISTS terminals             CASCADE;
    --TRUNCATE TABLE  terminals_export         CASCADE;
    '''

    cur.execute(sql)
    conn.commit()

def importdb(host,database,username,password,filepath):
    osm2pgsql_cmd = 'export PGPASSWORD={password} ; osm2pgsql --create --slim -E 3857 --cache-strategy sparse --cache 100 --host {host} --database {database} --username {username} {filepath}'.format(host=host,
    database=database,username=username,password=password,filepath=filepath)
    osm2pgsql_cmd += ' 2> /dev/null'
    logger.info(osm2pgsql_cmd)

    os.system(osm2pgsql_cmd)


def filter_routes(host,dbname,user,password):
    ConnectionString="dbname=" + dbname + " user="+ user + " host=" + host + " password=" + password

    try:
        conn = psycopg2.connect(ConnectionString)
    except:
        print('Unable to connect to the database')
        print(ConnectionString)
        return 0
    cur = conn.cursor()

    #TODO var
    cmd='''
ogr2ogr -overwrite    \
  "PG:host='''+host+''' dbname='''+dbname+''' user='''+user+''' password='''+password+'''" -nln red_zone \
     cfg/mostrans-bus_red_zone.geojson -t_srs EPSG:3857
    '''
    os.system(cmd)
    #выбираем веи, которые касаются красной зоны
    sql='''
    SELECT l.osm_id
FROM planet_osm_line l, red_zone
WHERE ST_Intersects(l.way , red_zone.wkb_geometry);'''
    cur.execute(sql)
    WaysInRedZone=[]
    rows = cur.fetchall()
    for row in rows:
        WaysInRedZone.append(str(row[0]))
        #удаляем релейшены, если в них есть веи, касающиеся красной зоны
        sql='''DELETE FROM planet_osm_rels WHERE members::VARCHAR LIKE CONCAT('%w',''' + str(row[0])+''','%') '''
        cur.execute(sql)
        conn.commit()
    #Удаление всех линий в красной зоне
    sql='''DELETE FROM planet_osm_line l
USING red_zone
WHERE ST_Intersects(l.way , red_zone.wkb_geometry);  '''
    cur.execute(sql)
    conn.commit()

    #Удаление всех маршрутов с пустым ref
    sql='''DELETE from planet_osm_rels  WHERE tags::VARCHAR NOT LIKE CONCAT('%ref,%')  '''
    cur.execute(sql)
    conn.commit()
    #Удаление всех веев, по которым не проходит маршрутов

def process(host,dbname,user,password):


        cmd='''python3 {path_osmot}/osmot/osmot.py --host {host} --database {dbname} --user {user} --password "{password}"
    '''.format(
                host=host,
                dbname=dbname,
                user=user,
                password=password,
                path_osmot=os.path.dirname(os.path.realpath(__file__))
        )
        logger.info(cmd)
        os.system(cmd)

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

        host=config.host
        dbname=config.dbname
        user=config.user
        password=config.password

        parser = argparser_prepare()
        args = parser.parse_args()

        filter_osm_dump(dump_path=args.dump_path, filter=args.filter,folder=args.output)
        os.system('export PGPASSWORD='+password)

        cleardb(host,dbname,user,password)
        importdb(host,dbname,user,password,os.path.join(args.output,FILTERED_DUMP_NAME))
        if (args.red_zone is not None): filter_routes(host,dbname,user,password)
        process(host,dbname,user,password)
        postgis2geojson(host,dbname,user,password,'terminals',folder=args.output)
        postgis2geojson(host,dbname,user,password,'routes',folder=args.output)

        #os.rename(os.path.join(args.output,'terminals_export.geojson'),os.path.join(args.output,'terminals.geojson'))
        #os.rename(os.path.join(args.output,'routes_with_refs.geojson'),os.path.join(args.output,'routes.geojson'))
