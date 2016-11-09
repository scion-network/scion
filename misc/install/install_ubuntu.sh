#!/bin/bash

# Update/upgrade packages
sudo apt-get update
#sudo apt-get upgrade -y

# See scioncc apt-get installs

sudo apt-get install -y --no-install-recommends libgeos-dev libgdal-dev gdal-bin libspatialindex-dev libblas-dev liblapack-dev libatlas-base-dev gfortran libfreetype6-dev
