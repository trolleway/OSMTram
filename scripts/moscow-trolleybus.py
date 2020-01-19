#!/usr/bin/python
# -*- coding: utf8 -*-

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


def download_osm_dump():

        if not os.path.exists('osm'):
            os.makedirs('osm')
        #TODO var
        os.system('wget --timestamping  https://s3.amazonaws.com/metro-extracts.mapzen.com/moscow_russia.osm.pbf')

def filter_osm_dump():
        import json
        import pprint
        pp=pprint.PrettyPrinter(indent=2)

        refs=[]
       
        print 'Filter step 1'
        #TODO var
        cmd='''
~/osmosis/bin/osmosis \
  -q \
  --read-pbf moscow_russia.osm.pbf \
  --tf accept-relations route=trolleybus \
  --used-way --used-node \
  --write-pbf routes.osm.pbf
'''
        os.system(cmd)

        print 'Filter step 3'
        cmd='''
~/osmosis/bin/osmosis \
  -q \
  --read-pbf routes.osm.pbf \
  --tf accept-relations "type=route" \
  --used-way --used-node \
  --write-pbf routesFinal.osm.pbf
    '''
        os.system(cmd)



def argparser_prepare():

    class PrettyFormatter(argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter):

        max_help_position = 35

    parser = argparse.ArgumentParser(description='',
            formatter_class=PrettyFormatter)
    parser.add_argument('--download', dest='download', action='store_true')
    parser.add_argument('--no-download', dest='download', action='store_false')
    parser.set_defaults(download=False)

    parser.epilog = \
        '''Samples:
%(prog)s --download
%(prog)s --no-download

''' \
        % {'prog': parser.prog}
    return parser

def cleardb(host,dbname,user,password):
    ConnectionString="dbname=" + dbname + " user="+ user + " host=" + host + " password=" + password

    try:

        conn = psycopg2.connect(ConnectionString)
    except:
        print 'I am unable to connect to the database                  ' 
        print ConnectionString
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
        print 'I am unable to connect to the database                  ' 
        print ConnectionString
        return 0
    cur = conn.cursor()

    #TODO var
    cmd='''
ogr2ogr -overwrite    \
  "PG:host='''+host+''' dbname='''+dbname+''' user='''+user+''' password='''+password+'''" -nln red_zone \
     cfg/mostrans-bus_red_zone.geojson -t_srs EPSG:3857
    '''
    print cmd
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
        print sql
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
        
        import time
        now = time.strftime("%c")
        print ("Current time %s"  % now )
        
        is_download = args.download
        
        if is_download == True:
            print "downloading"
            download_osm_dump()
        
        filter_osm_dump()
        os.system('export PGPASS='+password)

        cleardb(host,dbname,user,password)
        importdb(host,dbname,user,password)
        filter_routes(host,dbname,user,password) 
        process(host,dbname,user,password) 
        postgis2geojson(host,dbname,user,password,'terminals_export')
        postgis2geojson(host,dbname,user,password,'routes_with_refs')
