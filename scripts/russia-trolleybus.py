#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging
#import qgis_project_substitute

datafolder=''
dump_url = 'http://download.geofabrik.de/russia/northwestern-fed-district-latest.osm.pbf'
dump_filename = 'northwestern-fed-district-latest.osm.pbf'

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Start')

#перенести в core



cmd = 'python3 ../core/get_fresh_dump.py --url "http://download.geofabrik.de/russia/northwestern-fed-district-latest.osm.pbf" --output "../../tests/touchdown/rus-nw.osm.pbf"'
os.system(cmd)

#-------------
cmd = 'python3 ../core/process_basemap.py --dump_path ../../tests/touchdown/rus-nw.osm.pbf --bbox 31.0467,58.421,31.4765,58.6117 --output "../../tests/touchdown/" '
os.system(cmd)

#обрезка дампа троллейбусов
#cmd = '''osmconvert {dump_path} {bbox_string} --complete-ways --complex-ways -o={output_path_1}'''
#cmd = cmd.format(dump_path='../../tests/touchdown/rus-nw.osm.pbf',bbox_string='-b 31.0467,58.421,31.4765,58.6117', output_path_1='../../tests/touchdown/rus-nw-trolleybus.osm.pbf')

cmd = 'python3 ../core/process_routes.py --dump_path ../../tests/touchdown/rus-nw.osm.pbf --filter "route=trolleybus" --output "../../tests/touchdown/" '
logger.info(cmd)
os.system(cmd)
quit()
substitute_project(src='../qgis_project_templates/retrowave.qgs.template.qgs',dst = '../../tests/touchdown/out.qgs', layout_extent='''<Extent ymax="8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>''')

cmd = 'python3 ../core/pyqgis_client.py --project "../../tests/touchdown/out.qgs" --layout "Layout_retrowave_album" --output "../../tests/touchdown/Velikiy_Novgorod.png" '
os.system(cmd)
