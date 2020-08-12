#run

```
build backend container

docker build -t osmtram:1.0 .

#поднять контейнер с postgis
docker run --rm   --name backend_db -e POSTGRES_PASSWORD=user -e POSTGRES_USER=user -e POSTGRES_DB=gis -d -p 5432:5432   mdillon/postgis


 
#поднять и зайти в контейнер с ubuntu+python+gdal, в который проброшен порт с postgis
docker run -it --link backend_db:db -v ${PWD}/data:/data  -v ${PWD}:/OSMTram osmtram:1.0  /bin/bash
пути для win
docker run -it --link osmtram_backend_db:db -v c:\trolleway\OSMTram\data:/data  -v c:\trolleway\OSMTram:/OSMTram osmtram:1.0  /bin/bash

#внутри контейнера

Xvfb :1 -screen 0 800x600x24&
export DISPLAY=:1

cd scripts
python3 latvia-tram.py --workdir /data


```

# ver2
```
docker-compose up

в другом терминале
docker exec -ti osmtram_osmtramshell_1 /bin/bash

cd scripts
python3 latvia-tram.py --workdir /data
```


dbname=gis user=user host=server password=user

python3 ../core/process_routes.py --dump_path "/data/current_city.osm.pbf" --filter "route=tram" --output "/data/"




------
docker exec -ti osmtramshell /bin/bash
