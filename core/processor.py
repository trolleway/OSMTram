#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging
from osgeo import ogr
from osgeo import osr

#import sys
import stat
#sys.path.append("../core")
from qgis_project_substitute import substitute_project

import config

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class Processor:

    def make_layouts_poly(self,filepath):
        WORKDIR = '../data'
        #import layout geojson to postgis, and generating page bounds in all formats
        export_geojson = os.path.join(WORKDIR,'layout.geojson')
        
        cmd = 'ogr2ogr -overwrite -f "PostgreSQL" PG:"host={host} dbname={dbname} user={user} password={password}" -nln layouts "{filepath}"'
        cmd = cmd.format(host=config.host, dbname=config.dbname, user=config.user, password=config.password, filepath=filepath)
        logger.debug(cmd)
        os.system(cmd)
        
        # magic postgis process for generating poly file with lesser nodes count
        sql = 'DROP TABLE IF EXISTS layouts_poly0 ; CREATE TABLE layouts_poly0 AS SELECT ST_Transform(ST_Envelope(ST_Buffer(ST_Transform(wkb_geometry,3857),15000)),4326) AS wkb_geometry FROM layouts;'
        cmd = '''ogrinfo PG:"host={host} dbname={dbname} user={user} password={password}"  -sql '{sql}' '''
        cmd = cmd.format(host=config.host, dbname=config.dbname, user=config.user, password=config.password, sql=sql)
        logger.debug(cmd)
        os.system(cmd)

        sql = 'DROP TABLE IF EXISTS layouts_poly ; CREATE TABLE layouts_poly AS SELECT  b.wkb_geometry FROM     layouts_poly0 a,    (SELECT         (ST_Dump(St_multi(ST_Union(wkb_geometry)))).geom as wkb_geometry     FROM layouts_poly0) b WHERE    st_intersects(a.wkb_geometry, b.wkb_geometry) GROUP BY    b.wkb_geometry;'
        cmd = '''ogrinfo PG:"host={host} dbname={dbname} user={user} password={password}"  -sql '{sql}' '''
        cmd = cmd.format(host=config.host, dbname=config.dbname, user=config.user, password=config.password, sql=sql)
        logger.debug(cmd)
        os.system(cmd)
        
        
        os.remove(export_geojson) if os.path.exists(export_geojson) else None 
        cmd = '''ogr2ogr -overwrite -f "GeoJSON" {target} PG:"host={host} dbname={dbname} user={user} password={password}" -sql 'SELECT wkb_geometry FROM layouts_poly'  '''
        cmd = cmd.format(host=config.host, dbname=config.dbname, user=config.user, password=config.password, filepath=filepath,target=export_geojson)
        logger.debug(cmd)
        os.system(cmd)   
        os.chmod(export_geojson, 0o0777)    
        
        return 0
        
    def make_osmupdate_poly(self,filepath, folder):
        #import layout geojson to postgis, and generating polyfile
        
        target_filename=os.path.join(folder,'poly')
        geojson_filename = target_filename + '.geojson'
        
        cmd = 'ogr2ogr -overwrite -f "PostgreSQL" PG:"host={host} dbname={dbname} user={user} password={password}" -nln layouts "{filepath}"'
        cmd = cmd.format(host=config.host, dbname=config.dbname, user=config.user, password=config.password, filepath=filepath)
        logger.debug(cmd)
        os.system(cmd)
        
        # magic postgis process for generating poly file with lesser nodes count
        sql = 'DROP TABLE IF EXISTS layouts_poly0 ; CREATE TABLE layouts_poly0 AS SELECT ST_Transform(ST_Envelope(ST_Buffer(ST_Transform(wkb_geometry,3857),15000)),4326) AS wkb_geometry FROM layouts;'
        cmd = '''ogrinfo PG:"host={host} dbname={dbname} user={user} password={password}"  -sql '{sql}' '''
        cmd = cmd.format(host=config.host, dbname=config.dbname, user=config.user, password=config.password, sql=sql)
        logger.debug(cmd)
        os.system(cmd)

        sql = 'DROP TABLE IF EXISTS layouts_poly ; CREATE TABLE layouts_poly AS SELECT ST_ConcaveHull(ST_Collect(wkb_geometry), 0.99) AS wkb_geometry FROM layouts_poly0    ;'
        cmd = '''ogrinfo PG:"host={host} dbname={dbname} user={user} password={password}"  -sql '{sql}' '''
        cmd = cmd.format(host=config.host, dbname=config.dbname, user=config.user, password=config.password, sql=sql)
        logger.debug(cmd)
        os.system(cmd)
        
        os.remove(target_filename+'.geojson') if os.path.exists(target_filename+'.geojson') else None 
        cmd = '''ogr2ogr -overwrite -f "GeoJSON" {filename} PG:"host={host} dbname={dbname} user={user} password={password}" -sql 'SELECT wkb_geometry FROM layouts_poly'  '''
        cmd = cmd.format(host=config.host, dbname=config.dbname, user=config.user, password=config.password, filename=geojson_filename)
        logger.debug(cmd)
        os.system(cmd)   
        os.chmod(geojson_filename, 0o0777)   

        cmd = ''' python3 ../core/ogr2poly.py {src}'''
        cmd = cmd.format(src=geojson_filename)
        os.system(cmd)  
        
        os.unlink(geojson_filename)
        
        result_poly = os.path.join('../data','poly.poly')
        os.rename('poly_0.poly',os.path.join('../data','poly.poly'))
        os.chmod(result_poly, 0o0777)
        
        return result_poly
                   
    def get_bbox(self,filepath):
        #import layout geojson to postgis, and generating polyfile
        
        driver = ogr.GetDriverByName('GeoJSON')
        dataSource = driver.Open(filepath, 0) # 0 means read-only. 1 means writeable.
        layer = dataSource.GetLayer()
        extent = layer.GetExtent()
        
        lx = extent[0]
        ly = extent[2]
        rx = extent[1]
        ry = extent[3]
       
        bbox = '{lx},{ly},{rx},{ry}'.format(lx=lx,ly=ly,rx=rx,ry=ry)
        return bbox           

    def process_map(self,name,
    WORKDIR,
    bbox,
    dump_url,
    dump_name,
    poly,
    osmfilter_string='route=tram',
    layout_extent='<Extent ymax="8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>',
    prune=None,
    skip_osmupdate=None):

        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)

        filename = name+'.png'
        if prune == True:
            isprune = ' --prune '
        else:
            isprune = ''

        if skip_osmupdate == True:
            isskip_osmupdate = ' --skip-osmupdate '
        else:
            isskip_osmupdate = ''
            
        osmupdate_bbox = self.get_bbox('siberia.geojson')
        
        layouts_geojson = self.make_layouts_poly('siberia.geojson')
        result_poly = self.make_osmupdate_poly('siberia.geojson',WORKDIR)

        cmd = 'python3 ../core/get_fresh_dump.py --url "{url}" --output "{WORKDIR}/{dump_name}.osm.pbf" --bbox "{bbox}" {prune} {skip_osmupdate}'
        cmd = cmd.format(url=dump_url,WORKDIR=WORKDIR,bbox=osmupdate_bbox,POLY=result_poly,prune=isprune,skip_osmupdate=isskip_osmupdate,dump_name=dump_name)
        logger.info(cmd)
        os.system(cmd)
        
        
        cmd = 'python3 ../core/process_basemap.py --dump_path {WORKDIR}/{dump_name}.osm.pbf --bbox {bbox} -v --output "{WORKDIR}/" '
        cmd = cmd.format(WORKDIR=WORKDIR,bbox=bbox,dump_name=dump_name)
        logger.info(cmd)
        os.system(cmd)

        cmd = 'osmconvert "{WORKDIR}/{dump_name}.osm.pbf" -b={bbox} -o="{WORKDIR}/current_city.osm.pbf"'
        cmd = cmd.format(WORKDIR=WORKDIR,bbox=bbox,dump_name=dump_name)
        logger.info(cmd)
        os.system(cmd)

        cmd = 'python3 ../core/process_routes.py --dump_path "{WORKDIR}/current_city.osm.pbf" --filter "{osmfilter_string}" --output "{WORKDIR}/" '
        cmd = cmd.format(WORKDIR=WORKDIR,osmfilter_string=osmfilter_string)
        logger.info(cmd)
        os.system(cmd)
        
        fn = '{WORKDIR}/current_city.osm.pbf'.format(WORKDIR=WORKDIR)
        st = os.stat(fn)
        os.chmod(fn, 0o0777)
        
        fn = '{WORKDIR}/routes.osm.pbf'.format(WORKDIR=WORKDIR)
        st = os.stat(fn)
        os.chmod(fn, 0o0777)    

        substitute_project(
                        src='../qgis_project_templates/retrowave.qgs.template.qgs',
                        dst = WORKDIR+'/out.qgs',
                        layout_extent=layout_extent)

        cmd = 'python3 ../core/pyqgis_client.py --project "{WORKDIR}/out.qgs" --layout "4000x4000" --output "{png_file}" '
        cmd = cmd.format(WORKDIR=WORKDIR,png_file=os.path.join(os.path.realpath(WORKDIR),filename))
        logger.info(cmd)
        os.system(cmd)

