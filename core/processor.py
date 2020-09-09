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

    def reproject_4326_3857(self,x,y):
        from pyproj import Proj, transform
        
        inProj = Proj('epsg:4326')
        outProj = Proj('epsg:3857')
        
        xr,yr = transform(inProj,outProj,x,y)
        print(x,y,xr,yr)
        
        return xr,yr
    
    def make_geosjon_page(self,geom,geojson_page,code='pagename'):
        #make geojson file with one polygon
        # Save extent to a new Shapefile
        outDriver = ogr.GetDriverByName("GeoJSON")

        # Remove output shapefile if it already exists
        if os.path.exists(geojson_page):
            outDriver.DeleteDataSource(geojson_page)

        # Create the output shapefile
        outDataSource = outDriver.CreateDataSource(geojson_page)
        outLayer = outDataSource.CreateLayer("bound", geom_type=ogr.wkbPolygon)

        # Add an ID field
        codeField = ogr.FieldDefn("code", ogr.OFTString)
        outLayer.CreateField(codeField)

        # Create the feature and set values
        featureDefn = outLayer.GetLayerDefn()
        feature = ogr.Feature(featureDefn)
        feature.SetGeometry(geom)
        feature.SetField("code", code)
        outLayer.CreateFeature(feature)
        feature = None

        # Save and close DataSource
        outDataSource = None

    def get_layout_extent_by_geom(self,geom):
        #take ogr geom
        #return xml code for qgis layuout page 
        
        extent = geom.GetEnvelope()   
        lx = extent[0]
        ly = extent[2]
        rx = extent[1]
        ry = extent[3]           
        bbox = '{lx},{ly},{rx},{ry}'.format(lx=lx,ly=ly,rx=rx,ry=ry)
        
        x1_3857,y1_3857 = self.reproject_4326_3857(ly,lx)
        x2_3857,y2_3857 = self.reproject_4326_3857(ry,rx)
                           
        layout_extent = '''<Extent xmin="{xmin}" ymin="{ymin}" xmax="{xmax}" ymax="{ymax}"/>'''.format(
        xmin=round(x1_3857),
        ymin=round(y1_3857),
        xmax=round(x2_3857),
        ymax=round(y2_3857),
         )
         
        return layout_extent
        
        
    def process_sheets(self,geojson, WORKDIR, dump_name):
        #open sheets geojson
        from osgeo import ogr

        import os
        
        dump_url = 'http://download.geofabrik.de/russia/siberian-fed-district-latest.osm.pbf'


        driver = ogr.GetDriverByName("GeoJSON")
        dataSource = driver.Open(geojson, 0)
        layer = dataSource.GetLayer()

        '''src_source = osr.SpatialReference()
        src_source.ImportFromEPSG(4326)

        src_target = osr.SpatialReference()
        src_target.ImportFromEPSG(32637)
        transform = osr.CoordinateTransformation(src_source, src_target)'''

        #update dump
        osmupdate_bbox = self.get_bbox('siberia.geojson')
        
        layouts_geojson = self.make_layouts_poly('siberia.geojson')
        result_poly = self.make_osmupdate_poly('siberia.geojson',WORKDIR)

        cmd = 'python3 ../core/get_fresh_dump.py --url "{url}" --output "{WORKDIR}/{dump_name}.osm.pbf" --bbox "{bbox}" {prune} {skip_osmupdate}'
        cmd = cmd.format(url=dump_url,WORKDIR=WORKDIR,bbox=osmupdate_bbox,POLY=result_poly,prune='',skip_osmupdate='',dump_name=dump_name)
        logger.info(cmd)
        os.system(cmd)
        
        
        for feature in layer:
            geom = feature.GetGeometryRef()
            layout_extent = self.get_layout_extent_by_geom(geom)
            geojson_page = os.path.join(WORKDIR,'pagebound.geojson')
            self.make_geosjon_page(geom,geojson_page)
            
            extent = geom.GetEnvelope()   
            lx = extent[0]
            ly = extent[2]
            rx = extent[1]
            ry = extent[3]           
            bbox = '{lx},{ly},{rx},{ry}'.format(lx=lx,ly=ly,rx=rx,ry=ry)
                      
            sheet_name = str(feature.GetField('name_ru')) + ' ' + str(feature.GetField('type'))
            sheet_filename = feature.GetField('name_ru')
            bbox = bbox
            layout_extent = layout_extent
            filtersring = 'route='+str(feature.GetField('type'))
            
            #debugmsg = sheet_name +' ' + sheet_filename +' ' + bbox +' ' + layout_extent +' ' + filtersring
            #logger.debug(debugmsg)
            #quit()
            
            self.process_map(
    name=sheet_name,
    WORKDIR=WORKDIR,
    bbox=bbox, 
    layout_extent = layout_extent,
    osmfilter_string=filtersring,
    prune=False,
    dump_url=dump_url,
    dump_name='siberia',
    skip_osmupdate=False
    )
    
        layer.ResetReading()
        
        #for each record render map
        #pack to file
        
    def process_map(self,name,
    WORKDIR,
    bbox,
    dump_url,
    dump_name,
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

        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/out.qgs" --layout "4000x4000_atlas" --output "{png_file}" '
        cmd = cmd.format(WORKDIR=WORKDIR,png_file=os.path.join(os.path.realpath(WORKDIR),filename))
        logger.info(cmd)
        os.system(cmd)

