#run

```
build backend container

docker build -t osmtram:1.0 .

#поднять контейнер с postgis
docker run --rm   --name backend_db -e POSTGRES_PASSWORD=docker -d -p 5432:5432   mdillon/postgis

#поднять и зайти в контейнер с ubuntu+python+gdal, в который проброшен порт с postgis
docker run -it --link backend_db:server -v ${PWD}\:/data osmtram:1.0  /bin/bash
#внутри контейнера

#создать конфиг с паролем от postgis, пароль написан в первом шаге
cp config.example.py config.py 

```