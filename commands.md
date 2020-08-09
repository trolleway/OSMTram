#run

```
build backend container

docker build -t osmtram:1.0 .

#поднять контейнер с postgis
docker run --rm   --name backend_db -e POSTGRES_PASSWORD=user -e POSTGRES_USER=user -e POSTGRES_DB=gis -d -p 5432:5432   mdillon/postgis


 
#поднять и зайти в контейнер с ubuntu+python+gdal, в который проброшен порт с postgis
docker run -it --link backend_db:server -v ${PWD}/volumedata:/data  -v ${PWD}:/OSMTram osmtram:1.0  /bin/bash

#внутри контейнера

cd scripts
python3 latvia-tram.py --workdir /data

```


dbname=gis user=user host=server password=user

python3 ../core/process_routes.py --dump_path "/data/current_city.osm.pbf" --filter "route=tram" --output "/data/"
