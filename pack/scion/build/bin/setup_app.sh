#!/bin/bash

source ~/.bash_profile
workon scion

cd $CODE_DIR
git clone https://github.com/scion-network/scion

cd $APP_DIR
sed 's/git\@github\.com\:/https\:\/\/github\.com\//' .gitmodules > .gitmodules1
mv .gitmodules1 .gitmodules
git submodule update --init


# Buildout dependencies
python bootstrap.py -v 2.3.1
bin/buildout

bin/generate_interfaces

