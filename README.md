# OSMTram
Generate transit maps from OSM data in docker


<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

There are many great public transport routing services online, however, I stil need static maps of public transit lines. I want to create a automatic process for generate static maps from OpenStreetMap data, with simply running routine.

Here's why:
* Changes of public transport lines become quickly, but transit authorities news resourses do not provide up-to-date maps, only text descriptions.
* Public transport routing services solve one problem: how to get to specific address. A map of all lines solve diffirent problem: where i can go from some point.
* Old maps may disappear from Internet, due to closed licensing, and no one can copy it. A maps generated from OpenStreetMap keep open license, and can be reproduced to many resources.
* Public Transport lines information in OSM keeps from 2010-s, so historical map generation already possible.

A data features, needed to orientation by static public transport map is

1. Geometry of lines, with route refs
2. Places of terminus, with route refs and names.
3. Directions for one-line lines.
4. Interval information, or marking of low interval lines.
5. Date of map source.
6. Good looking basemap withouth distracting map features, like "boundary of national parks".

This scripts provive points 1, 2, 3, calculating from OSM data. And also 5 and 6.

### Built With
This section should list any major frameworks that you built your project using. Leave any add-ons/plugins for the acknowledgements section. Here are a few examples.
* [PostGIS](https://postgis.net/)
* [Docker](https://www.docker.com/)
* [Python](https://www.python.org/)
* [QGIS] (https://qgis.org/)



## Getting Started


### Installation in docker (prod)

This script run in Docker container, witch can be run on any modern OS.

Install git. Here is git submodules, download zip from github will not work. See https://github.com/git-guides/install-git

```
git clone  --recurse-submodules https://github.com/trolleway/OSMTram.git
cd OSMTram
docker build -t osmtram:1.0 .

#start postgis container
docker run --rm   --name osmtram_backend_db -e POSTGRES_PASSWORD=user -e POSTGRES_USER=user -e POSTGRES_DB=gis -d -p 5432:5432   mdillon/postgis

#start and go to container with ubuntu+python+gdal, with network link to postgis
docker run --rm -it --link osmtram_backend_db:db -v ${PWD}/data:/data   osmtram:1.0  /bin/bash
# on Windows run in powershell
```

# Into container
```
time python3 run.py russia.json --workdir /data  --basemap-caching --where "name_int='Volgograd' and route='tram'"
```

### Installation in docker (develop)
Same as prod, but mount code folder to container, no need to rebuild container at code change

```
git clone  --recurse-submodules https://github.com/trolleway/OSMTram.git
cd OSMTram
docker build -f Dockerfiledev -t osmtram:dev .


#run postgis in docker
docker run --rm   --name osmtram_backend_db -e POSTGRES_PASSWORD=user -e POSTGRES_USER=user -e POSTGRES_DB=gis -d -p 5432:5432   mdillon/postgis

#win
docker run --rm -it --link osmtram_backend_db:db -v ${PWD}/data:/data -v ${PWD}:/OSMTram osmtram:dev  /bin/bash
```


## Examples

```
time python3 run.py italy-sud.metadata.json --workdir /data
time python3 run.py poland.json --skip-osmupdate --workdir /data --where "name_int = 'Gdansk'"
time python3 run.py russia.json --skip-osmupdate --basemap-caching --workdir /data --where "name_int = 'Ekaterinburg' and route='tram'"
time python3 run.py russia.json --basemap-caching --workdir /data --where "name_int = 'Ekaterinburg' and route='trolleybus'"
time python3 run.py russia.json --skip-osmupdate --workdir /data --where "not valid"

```

## Edit map style

1. Download QGIS and open one of .qgs projects in /qgis_project_templates/
2. There is sample data layers for some typical city. You can edit layers symbolics and label properties. 
3. Overwrite .qgs project or save to new project and add refrences into core/processor.py

At next run a map will rendered using changed project. 





This is a docker container. It uses for input a bbox, filter string and map style, and generate a png image file.

It consists from there scripts:

* core/dump_prepare.py - Takes a url or pbf file, poly file, filter string, and filtering it to basemap.pbf and pt_data.pbf. Use osmfilter.
* core/historical_dump.py - Download and prepare historical dump for dump_prepare. May will be run outside container, due to huge size of dumps. Use osmupdate and osmfilter.
* core/basemap_process.py - Generate image of basemap for bbox. Importing basemap.pbf to postgis, create QGIS Server WMS, make png from WMS.
* core/pt_data_process.py - Generate image of public transport map

* core/pyqgis_client_atlas.py - render pdf/svg/png map using standart qgis project with atlas layout. Extent is set in geojson file.
    One run generate one-page atlas, then pages combined in multi-page pdf or zip archive
    
    Script start QGIS in docker container, make copy of QGIS project from /qgis_project_templates, put data layers into gpkg files, and run QGIS operation "Atlas rendering"

### Deprecated scripts, should be removed

* core/pyqgis_client.py
* core/qgis_project_substitute.py
## Contact

Artem Svetlov - [@trolleway](https://twitter.com/trolleway) - trolleway@yandex.ru


