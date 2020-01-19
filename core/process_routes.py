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

# move all magic variables to up

DUMP_URL = 'https://s3.amazonaws.com/metro-extracts.mapzen.com/moscow_russia.osm.pbf'
FILTER = '--tf accept-relations route=trolleybus'
#Будут удалены маршруты, проходящие через red_zone, то есть междугородные.
RED_ZONE = 'cfg/mostrans-bus_red_zone.geojson'

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

def filter_osm_dump(dump_path, filter, folder):
        import json
        import pprint
        pp=pprint.PrettyPrinter(indent=2)

        refs=[]
        output_path_1 = os.path.join(folder,'routes1.osm.pbf')
        output_path_2 = os.path.join(folder,'routesFinal.osm.pbf')

        #TODO var
        cmd='''
~/osmosis/bin/osmosis \
  -q \
  --read-pbf {dump_path} \
  {filter} \
  --used-way --used-node \
  --write-pbf {output_path_1}
'''
        cmd = cmd.format(dump_path = dump_path, filter = filter, output_path_1 = output_path_1)
        os.system(cmd)

        cmd='''
~/osmosis/bin/osmosis \
  -q \
  --read-pbf {output_path_1} \
  --tf accept-relations "type=route" \
  --used-way --used-node \
  --write-pbf {output_path_2}
    '''
        cmd = cmd.format(output_path_1 = output_path_1, output_path_2 = output_path_2)
        os.system(cmd)

        os.unlink(output_path_1)





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
    print ('Database wiped')

def importdb(host,database,username,password):
    os.system('osm2pgsql --create --slim -E 3857 --cache-strategy sparse --cache 100 --host {host} --database {database} --username {username} routesFinal.osm.pbf'.format(host=host,
    database=database,username=username,password=password))


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

        cmd='''python osmot/osmot.py -hs {host} -d {dbname} -u {user} -p {password}
    '''.format(
                host=host,
                dbname=dbname,
                user=user,
                password=password
        )
        os.system(cmd)

def postgis2geojson(host,dbname,user,password,table):
    if os.path.exists(table+'.geojson'):
        os.remove(table+'.geojson')

    cmd='''
ogr2ogr -f GeoJSON '''+table+'''.geojson    \
  "PG:host='''+host+''' dbname='''+dbname+''' user='''+user+''' password='''+password+'''" "'''+table+'''"
    '''
    print(cmd)
    os.system(cmd)

if __name__ == '__main__':

        host=config.host
        dbname=config.dbname
        user=config.user
        password=config.password

        parser = argparser_prepare()
        args = parser.parse_args()


        filter_osm_dump(dump_path=args.dump_path, filter=args.filter,folder=args.folder)
        os.system('export PGPASS='+password)

        cleardb(host,dbname,user,password)
        importdb(host,dbname,user,password)
        filter_routes(host,dbname,user,password)
        process(host,dbname,user,password)
        postgis2geojson(host,dbname,user,password,'terminals_export')
        postgis2geojson(host,dbname,user,password,'routes_with_refs')
