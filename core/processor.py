#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging
from osgeo import ogr
from osgeo import osr
import subprocess


#import sys
import stat
#sys.path.append("../core")
from qgis_project_substitute import substitute_project

import shutil
import zipfile

import config

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class Processor:

    def make_layouts_poly(self,filepath,WORKDIR):
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

        result_poly = os.path.join(folder,'poly.poly')
        shutil.move('poly_0.poly',os.path.join(folder,'poly.poly'))
        #os.rename only works if source and destination are on the same file system. You should use shutil.move instead.
        os.chmod(result_poly, 0o0777)

        return result_poly

    def get_bbox(self,filepath):
        #import layout geojson to postgis, and generating polyfile

        driver = ogr.GetDriverByName('GeoJSON')
        dataSource = driver.Open(filepath, 0) # 0 means read-only. 1 means writeable.
        layer = dataSource.GetLayer()
        extent = layer.GetExtent()

        # Create a Polygon from the extent tuple
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(extent[0],extent[2])
        ring.AddPoint(extent[1], extent[2])
        ring.AddPoint(extent[1], extent[3])
        ring.AddPoint(extent[0], extent[3])
        ring.AddPoint(extent[0],extent[2])
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        extent = poly.Buffer(0.7).GetEnvelope()

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

    def make_zip_bymask(dirname, filename, mask):
        import subprocess

        subprocess.call(['zip', '-j', os.path.join(dirname,filename)] + glob.glob(os.path.join(dirname,mask)))

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


    def process_sheets(self,geojson, WORKDIR, dump_url, dump_name, attribute_filter = '', osmupdate_mode = '', skip_osmupdate = None, basemap_caching = False):
        #open sheets geojson
        from osgeo import ogr
        import os

        assert os.path.isfile(geojson)

        driver = ogr.GetDriverByName("GeoJSON")
        dataSource = driver.Open(geojson, 0)
        layer = dataSource.GetLayer()
        if attribute_filter != '': layer.SetAttributeFilter(attribute_filter)
        featureCount = layer.GetFeatureCount()
        if featureCount < 1:
            logger.warning('No records found with filter '+attribute_filter + ' in file ' + geojson)
            quit('stopping')

        #update dump
        osmupdate_bbox = self.get_bbox(geojson)

        layouts_geojson = self.make_layouts_poly(geojson,WORKDIR)
        result_poly = self.make_osmupdate_poly(geojson,WORKDIR)

        if osmupdate_mode == 'hour':
            mode = '--mode hour'
        elif osmupdate_mode == 'minute':
            mode = '--mode minute'
        elif osmupdate_mode == 'day':
            mode = '--mode day'
        else:
            mode = ''

        assert skip_osmupdate is None or skip_osmupdate == True

        if skip_osmupdate:
            s = '--skip-osmupdate'
        else:
            s = ''

        cmd = 'python3 ../core/get_fresh_dump.py --url "{url}" --output "{WORKDIR}/{dump_name}.osm.pbf" --bbox "{bbox}" {mode} {prune} {skip_osmupdate}'
        cmd = cmd.format(url=dump_url,WORKDIR=WORKDIR,bbox=osmupdate_bbox,POLY=result_poly,prune='',skip_osmupdate=s,dump_name=dump_name, mode=mode)
        logger.info(cmd)
        os.system(cmd)

        cmd = 'rm /data/*.pdf'
        os.system(cmd)
        for feature in layer:
            sheet_name = str(feature.GetField('name_loc')) + ' ' + str(feature.GetField('route'))
            geom = feature.GetGeometryRef()
            layout_extent = self.get_layout_extent_by_geom(geom)
            geojson_page = os.path.join(WORKDIR,'pagebound.geojson')
            self.make_geosjon_page(geom,geojson_page,sheet_name)

            extent = geom.Buffer(0.7).GetEnvelope()
            lx = extent[0]
            ly = extent[2]
            rx = extent[1]
            ry = extent[3]
            bbox = '{lx},{ly},{rx},{ry}'.format(lx=lx,ly=ly,rx=rx,ry=ry)

            sheet_filename = feature.GetField('name_loc')
            bbox = bbox
            layout_extent = layout_extent
            filtersrc = ''
            filtersring = 'route='+str(feature.GetField('route'))
            try:
                filtersrc = str(feature.GetField('filter'))
            except:
                pass

            if (filtersrc != '' and filtersrc is not None and filtersrc != 'None'): filtersring = filtersrc

            logger.info(sheet_name)



            wtext = '''
{{Map
|description=$desc$
|date=$date$
|map_date={{other date|after|2021}}
|location=$location$
|projection=EPSG:3857
|heading=N
|latitude=$lat$
|longitude=$lon$
|source={{own}}
|author={{Creator:Artem Svetlov}}
|permission=
|other versions=
}}

=={{int:license-header}}==
{{OpenStreetMap}}

[[Category:Maps of $location$]]
[[Category:Maps by OSMTram]]
            '''
            if 'tram' in filtersring: wtext+="[[Category:Tram transport in $location$]]\n[[Category:Trams in $location$]]"
            if 'trolleybus' in filtersring: wtext+="[[Category:Trolleybuses in $location$]]"


            self.process_map(
            name=sheet_name,
            WORKDIR=WORKDIR,
            bbox=bbox,
            layout_extent = layout_extent,
            osmfilter_string=filtersring,
            dump_url=dump_url,
            dump_name=dump_name,
            basemap_caching = basemap_caching
            )

            transport_ru_genitive={'trolleybus':'троллейбуса','tram':'трамвая','subway':'метро'}
            from datetime import date
            today = date.today()
            try:
                #if all attributes not null

                desc = '{{ru|1=Карта маршрутов '+transport_ru_genitive.get(feature['route'],'')+' в городе '+feature['name_loc']+'}}{{en|1=Map of '+feature['name_int']+' '+feature['route']+" lines \n Generated with script https://github.com/trolleway/OSMTram automatically from OpenStreetMap dump \n Ask me for update map}} {{ Created with QGIS|v }} "
            except:
                desc = '{{ru|1=Карта  '+feature['route']+'}}{{en|1=Map of  '+feature['route']+'}}'
            wtext = wtext.replace('$desc$', desc)
            wtext = wtext.replace('$date$',today.strftime("%Y-%m-%d"))
            if feature['name_int'] is not None:
                wtext = wtext.replace('$location$', feature['name_int'])
            else:
                wtext = wtext.replace('$location$', feature['name_loc'])
            wtext = wtext.replace('$lat$', str(round(geom.Centroid().GetY(),2)))
            wtext = wtext.replace('$lon$', str(round(geom.Centroid().GetX(),2)))


            filename=os.path.join(os.path.realpath(WORKDIR),''+sheet_name+'_wikitext.txt')
            with open(filename, 'w') as f: f.write(wtext)


        layer.ResetReading()
        from datetime import date

        today = date.today()
        d1 = today.strftime("%Y-%m-%d")

        atlas_filename = 'Трамвайные и троллейбусные маршруты России. Атлас ' + d1

        cmd = 'pdfunite /data/*.pdf "/data/'+atlas_filename+'.pdf"'
        os.system(cmd)

        #self.make_zip_bymask(dirname = WORKDIR, filename = atlas_filename + '_svg.zip', mask = '.svg')

        #for each record render map
        #pack to file

    def process_map(self,name,
    WORKDIR,
    bbox,
    dump_url,
    dump_name,
    osmfilter_string='route=tram',
    layout_extent='<Extent ymax="8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>',
    basemap_caching = False):

        BASEMAP_CACHE_DIR = os.path.join(WORKDIR,'BASEMAP_CACHE')

        filename = name+'.pdf'

        skip_process_basemap = False
        # check if basemap data exists
        basemap_cache_filename = os.path.join(BASEMAP_CACHE_DIR,name)+'.zip'
        if basemap_caching and os.path.exists(BASEMAP_CACHE_DIR):
            logger.debug('cache dir exist')
            basemap_cache_filename = os.path.join(BASEMAP_CACHE_DIR,name)+'.zip'
            if os.path.exists(basemap_cache_filename):
                logger.debug('cache archive exist')
                zip_file = zipfile.ZipFile(basemap_cache_filename)


                if zip_file.testzip() is None :  #returns none if archive ok, or name of frist bad file
                    logger.debug('zip file tested')
                    zip_file.extractall(WORKDIR)
                    logger.info('basemap extracted from cache')
                    skip_process_basemap = True

        if not skip_process_basemap:
            cmd = 'python3 ../core/process_basemap.py --dump_path {WORKDIR}/{dump_name}.osm.pbf --bbox {bbox} --output "{WORKDIR}/" ' # --verbose is allowed
            cmd = cmd.format(WORKDIR=WORKDIR,bbox=bbox,dump_name=dump_name)
            logger.info(cmd)
            os.system(cmd)

        #store basemap data in cache
        if basemap_caching:
            if not os.path.exists(BASEMAP_CACHE_DIR):
                os.makedirs(BASEMAP_CACHE_DIR)
            basemap_files_name = ('highway.gpkg','land.gpkg','landuse.gpkg','railway.gpkg','water.gpkg')
            basemap_files = list()
            for element in basemap_files_name:
                basemap_files.append(os.path.join(os.path.realpath(WORKDIR),element))

            self.archive_files(basemap_files,target=basemap_cache_filename)


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
                        dst = WORKDIR+'/retrowave.qgs',
                        layout_extent=layout_extent)
        substitute_project(
                        src='../qgis_project_templates/tinyblack.qgs.template.qgs',
                        dst = WORKDIR+'/tinyblack.qgs',
                        layout_extent=layout_extent)
        substitute_project(
                        src='../qgis_project_templates/wikipedia.qgs.template.qgs',
                        dst = WORKDIR+'/wikipedia.qgs',
                        layout_extent=layout_extent)
        substitute_project(
                        src='../qgis_project_templates/wikipedia-simpler.qgs.template.qgs',
                        dst = WORKDIR+'/wikipedia-simpler.qgs',
                        layout_extent=layout_extent)
        substitute_project(
                        src='../qgis_project_templates/manila.qgs.template.qgs',
                        dst = WORKDIR+'/manila.qgs',
                        layout_extent=layout_extent)

        files4zip = list()
        files4zip = ['manila.qgs',
        'tinyblack.qgs',
        'wikipedia.qgs',
        'wikipedia-simpler.qgs',
        'routes.geojson',
        'pagebound.geojson',
        'terminals.geojson',
        'landuse.gpkg',
        'highway.gpkg',
        'railway.gpkg',
        'water.gpkg',
        'land.gpkg',
        ]

        #if os.path.isfile('chronodata.gpkg'): os.remove('chronodata.gpkg')
        #if os.path.isfile('notes_now.gpkg'): os.remove('notes_now.gpkg')

        fn = None
        if 'trolleybus' in osmfilter_string: fn='trolleybus_street_labels.gpkg'
        if 'tram' in osmfilter_string: fn='tram_street_labels.gpkg'

        if fn is not None:
            cmd = 'ogr2ogr -overwrite -clipsrc '+bbox.replace(',',' ')+' -nlt multilinestring -nln street_labels ' + WORKDIR+'/street_labels.gpkg  '+fn + ' street_labels'
            logger.info(cmd)
            os.system(cmd)
            files4zip.append('street_labels.gpkg')

        filename = os.path.join(os.path.realpath(WORKDIR),name+'.pdf')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/manila.qgs" --layout "4000x4000_atlas" --output "{filename}"   > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.debug(cmd)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)

        filename = os.path.join(os.path.realpath(WORKDIR),'tinyblack4000_'+name+'.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/tinyblack.qgs" --layout "4000x4000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.debug(cmd)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)

        filename=os.path.join(os.path.realpath(WORKDIR),''+name+'_map_kakava4000.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/manila.qgs" --layout "4000x4000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.debug(cmd)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)

        filename=os.path.join(os.path.realpath(WORKDIR),''+name+'_map_kakava2000.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/manila.qgs" --layout "2000x2000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.debug(cmd)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)

        filename=os.path.join(os.path.realpath(WORKDIR),''+name+'_map_kakava1000.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/manila.qgs" --layout "1000x1000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)


        filename=os.path.join(os.path.realpath(WORKDIR),''+name+'_wikipedia4000.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/wikipedia.qgs" --layout "4000x4000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)


        cmd = 'ogr2ogr -overwrite -clipsrc '+bbox.replace(',',' ')+' -nlt point  ' + WORKDIR+'/notes_now.gpkg notes_now_trolleybus.gpkg'
        logger.info(cmd)
        os.system(cmd)
        files4zip.append('notes_now.gpkg')

        filename=os.path.join(os.path.realpath(WORKDIR),''+name+'_map_kakava1000_notes.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/manila.qgs" --layout "1000x1000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)

        filename=os.path.join(os.path.realpath(WORKDIR),''+name+'_map_kakava2000_notes.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/manila.qgs" --layout "2000x2000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)

        filename=os.path.join(os.path.realpath(WORKDIR),''+name+'_map_kakava4000_notes.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/manila.qgs" --layout "2000x2000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)


        #hook for historical lines
        #copy map data here, and render with same qgis projects
        fn = None
        if 'trolleybus' in osmfilter_string: fn='trolleybus lines.gpkg'
        if 'tram' in osmfilter_string: fn='tram lines.gpkg'

        cmd = 'ogr2ogr -overwrite -clipsrc '+bbox.replace(',',' ')+' -nlt multilinestring -nln chronolines ' + WORKDIR+'/chronolines.gpkg "'+fn+'" lines'
        logger.info(cmd)
        os.system(cmd)
        files4zip.append('chronolines.gpkg')

        # text2wikimedia commons

        filename=os.path.join(os.path.realpath(WORKDIR),''+name+'_map_closed_lines_4000.svg')
        cmd = 'python3 ../core/pyqgis_client_atlas.py --project "{WORKDIR}/manila.qgs" --layout "4000x4000_atlas" --output "{filename}"  > /dev/null 2>&1'
        cmd = cmd.format(WORKDIR=WORKDIR,filename=filename)
        logger.debug(cmd)
        logger.info(filename)
        os.system(cmd)
        files4zip.append(filename)


        files4zip_new = list()
        for element in files4zip: files4zip_new.append(os.path.join(os.path.realpath(WORKDIR),element))
        files4zip = files4zip_new
        zip_filename = os.path.join(os.path.realpath(WORKDIR),name+'.BUNDLE.ZIP')
        self.archive_files(files4zip,zip_filename)
        #clean dir
        for element in files4zip:
            if os.path.isfile(element):
                if not element.endswith('kakava4000.svg'):
                    os.remove(element)

    def archive_files(self,files,target):
        print('pack '+target)
        zipObj = zipfile.ZipFile(target, 'w')
        # Add multiple files to the zip
        for element in files:
            if os.path.isfile(element):
                zipObj.write(element,arcname=os.path.basename(element))

        # close the Zip File
        zipObj.close()
