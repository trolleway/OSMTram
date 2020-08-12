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



class Processor:

    def make_poly(self,filepath):
        driver = ogr.GetDriverByName("GeoJSON")
        dataSource = driver.Open(filepath, 0)
        layer = dataSource.GetLayer()
        
        new_driver = ogr.GetDriverByName("GeoJSON")
        new_data_source = new_driver.CreateDataSource("poly.geojson")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        new_layer = new_data_source.CreateLayer("poly", srs, ogr.wkbPolygon)
        
        for feature in layer:
            new_feature = ogr.Feature(new_layer.GetLayerDefn())
            geom = feature.GetGeometryRef().Buffer(0.01).GetEnvelope()
            print("minX: %r, minY: %r, maxX: %r, maxY: %r" %(geom[0],geom[2],geom[1],geom[3]))
            
            new_feature.SetGeometry(geom)
            new_layer.CreateFeature(new_feature)
            new_feature = None
        new_data_source = None
            
        layer.ResetReading()

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
            
        #self.make_poly('siberia.geojson')



        cmd = 'python3 ../core/get_fresh_dump.py --url "{url}" --output "{WORKDIR}/{dump_name}.osm.pbf" --poly "{POLY} {prune} {skip_osmupdate}"'
        cmd = cmd.format(url=dump_url,WORKDIR=WORKDIR,bbox=bbox,POLY=poly,prune=isprune,skip_osmupdate=isskip_osmupdate,dump_name=dump_name)
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

