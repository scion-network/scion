===========================================================
Dockerfile repository for the Scientific Observatory Network
===========================================================


Docker image and docker-compose system start.


IMAGES
======

scion:          Based on scioncc/scion_cc

Requires scion_pg and scion_rabbitmq

See image directories/README for details


USAGE
=====

See image README files for image build instructions.

To run a system using docker-compose:

cd pack
docker-compose -f dc/dc-scion.yml -d up
docker-compose -f dc/dc-scion.yml down
docker-compose -f dc/dc-scion.yml restart cc
docker-compose -f dc/dc-scion.yml logs cc

docker exec -it dc_cc_1 /bin/bash -l

# Manhole into running ScionCC (exit with Ctrl-D)
docker exec -it cc bash -l bin/manhole

