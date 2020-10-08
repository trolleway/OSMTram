FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN apt-get update && apt-get install --no-install-recommends -y mc git nano wget tree
ARG uid=1000
ARG gid=1000
RUN groupadd -g $gid trolleway && useradd --home /home/trolleway -u $uid -g $gid trolleway  \
  && mkdir -p /home/trolleway && chown -R trolleway:trolleway /home/trolleway
RUN echo 'trolleway:user' | chpasswd

#у меня в деревне такой инет, что сразу все зависимости не выкачиваются, и этот уровень завершается.
#попробую ставить зависимости по частям, чтоб меньше качать
RUN apt-get install --no-install-recommends -y proj-data
RUN apt-get install --no-install-recommends -y python3-numpy
RUN apt-get install --no-install-recommends -y gdal-bin

RUN apt-get install --no-install-recommends -y python3-pip
RUN apt-get install --no-install-recommends -y python3-psycopg2
RUN apt-get install --no-install-recommends -y time
RUN apt-get install --no-install-recommends -y osm2pgsql osmctools aria2 zip
RUN pip3 install tqdm
RUN apt-get install --no-install-recommends -y  qgis python3-qgis  
RUN apt-get install --no-install-recommends -y  xvfb
RUN apt-get install --no-install-recommends -y  poppler-utils

#add to sudoers
RUN apt-get install -y apt-utils
RUN apt-get install -y sudo
RUN adduser trolleway sudo
RUN usermod -aG sudo trolleway

ADD https://api.github.com/repos/trolleway/OSMTram/git/refs/heads/master   ver.json
#The API call will return different results when the head changes, invalidating the docker cache

RUN git clone --recurse-submodules https://github.com/trolleway/OSMTram.git

RUN chmod  --recursive 777 /OSMTram

RUN mkdir /OSMTram/volumedata
WORKDIR /OSMTram




# Создание конфигов с захардкодеными адресами
# COPY configs4docker/.pgpass /osmtram_preprocessing/.pgpass
#COPY configs4docker/config.cfg /osmtram_preprocessing/config.cfg
#COPY configs4docker/osmosis_creds.cfg /osmtram_preprocessing/osmosis_creds.cfg
