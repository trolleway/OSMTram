#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import logging

import sys
sys.path.append("../core")
from qgis_project_substitute import substitute_project

WORKDIR='/media/trolleway/elvideo/osmtram'
POLY='russia-trolleybus.poly'
dump_url = 'http://download.geofabrik.de/russia/northwestern-fed-district-latest.osm.pbf'
dump_url = 'http://download.geofabrik.de/russia/volga-fed-district-latest.osm.pbf'
dump_url = 'http://download.geofabrik.de/russia/kaliningrad-latest.osm.pbf'



logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Start')

#перенести в core
def process_map(name,WORKDIR,bbox,layout_extent='<Extent ymax="8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>'):

    filename = name+'.png'

    cmd = 'python3 ../core/get_fresh_dump.py --url "{url}" --output "{WORKDIR}/rus-nw.osm.pbf" --poly "{POLY}"'
    cmd = cmd.format(url=dump_url,WORKDIR=WORKDIR,bbox=bbox,POLY=POLY)
    os.system(cmd)
    #quit()

    #-------------
    cmd = 'python3 ../core/process_basemap.py --dump_path {WORKDIR}/rus-nw.osm.pbf --bbox {bbox} --output "{WORKDIR}/" '
    cmd = cmd.format(WORKDIR=WORKDIR,bbox=bbox)
    os.system(cmd)

    cmd = 'osmconvert "{WORKDIR}/rus-nw.osm.pbf" -b={bbox} -o="{WORKDIR}/current_city.osm.pbf"'
    cmd = cmd.format(WORKDIR=WORKDIR,bbox=bbox)
    os.system(cmd)

    cmd = 'python3 ../core/process_routes.py --dump_path "{WORKDIR}/current_city.osm.pbf" --filter "route=trolleybus" --output "{WORKDIR}/" '
    cmd = cmd.format(WORKDIR=WORKDIR)
    logger.info(cmd)
    os.system(cmd)

    substitute_project(
                    src='../qgis_project_templates/retrowave.qgs.template.qgs',
                    dst = WORKDIR+'/out.qgs',
                    layout_extent=layout_extent)

    cmd = 'python3 ../core/pyqgis_client.py --project "{WORKDIR}/out.qgs" --layout "layout_retrowave_album" --output "{png_file}" '
    cmd = cmd.format(WORKDIR=WORKDIR,png_file=os.path.join(os.path.realpath(WORKDIR),filename))
    logger.info(cmd)
    os.system(cmd)

cities = list()
#cities.append({'name':'Veliky_Novgorod','bbox':'31.0467,58.421,31.4765,58.6117','layout_extent':'''<Extent ymax="8089470" xmax="3489740" xmin="3469769" ymin="8075350"/>'''})
#cities.append({'name':'Petrozavodsk','bbox':'34.2809,61.7473,34.4622,61.8187','layout_extent':'''<Extent xmax="3837010.00714727956801653" xmin="3814612.03897902462631464" ymin="8800347.35082474164664745" ymax="8816184.03821748681366444"/>'''})
#cities.append({'name':'Murmansk','bbox':'32.9329,68.8745,33.2941,69.0641','layout_extent':'''<Extent xmax="3722126" xmin="3646811" ymin="10710797" ymax="10764050"/>'''})
#cities.append({'name':'Vologda','bbox':'39.6604,59.1689,40.023,59.2994','layout_extent':'''<Extent xmax="4451269" xmin="4429472" ymin="8218346" ymax="8233757"/>'''})
#cities.append({'name':'Saint-Petersburg','bbox':'29.9997,59.7816,30.6396,60.1117','layout_extent':'''<Extent xmax="3415025" xmin="3331990" ymin="8356650" ymax="8415361"/>'''})
#cities.append({'name':'Tolyatti','bbox':'49.192815,53.415604,49.652226,53.597258','layout_extent':'''<Extent xmax="5513789" xmin="5479632" ymin="7067270" ymax="7091421"/>'''})

cities.append({'name':'Kaliningrad','bbox':'20.356018,54.6532,20.61248,54.77497','layout_extent':'''<Extent xmax="2316424" xmin="2219158" ymin="7280359" ymax="7330158"/>'''})


for city in cities:
    #print(city['name'])
    process_map(name=city['name'],WORKDIR=WORKDIR,bbox=city['bbox'], layout_extent = city['layout_extent'])


#process_map(name='Veliky_Novgorod',WORKDIR=WORKDIR,bbox='31.0467,58.421,31.4765,58.6117', layout_extent = '''<Extent ymax="8087642" xmax="3487345" xmin="3470799" ymin="8075943"/>''')
