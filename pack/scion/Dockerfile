FROM scioncc/scion_cc:latest
MAINTAINER Michael Meisinger <michael.meisinger@gmail.com>

ENV APP_NAME=scion APP_DIR=$CODE_DIR/scion

# Special libs for Scipy, geospatial etc
RUN apt-get install -y --no-install-recommends \
        libgeos-dev libgdal-dev gdal-bin libspatialindex-dev \
        libblas-dev liblapack-dev libatlas-base-dev gfortran libfreetype6-dev

ADD pack/scion/build/bin/setup_app.sh $BIN_DIR
RUN chmod -R +x $BIN_DIR

RUN bash $BIN_DIR/setup_app.sh

ADD pack/scion/run $HOME
RUN chmod -R +x $BIN_DIR
