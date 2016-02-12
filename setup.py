#!/usr/bin/env python

from setuptools import setup, find_packages

import os
import sys

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def get_data_dirs(path, patterns):
    data_dirs = [(rt+"/"+dn+"/") for rt, ds, fs in os.walk(path) for dn in ds]
    data_dir_patterns = []
    for pat in patterns:
        data_dir_patterns += [(dn+pat)[len(path)+1:] for dn in data_dirs]
    return data_dir_patterns

# Add /usr/local/include to the path for macs, fixes easy_install for several packages (like gevent and pyyaml)
if sys.platform == 'darwin':
    os.environ['C_INCLUDE_PATH'] = '/usr/local/include'

VERSION = read("VERSION").strip()

# Flag that includes ScionCC code in this egg
INCLUDE_SCIONCC = False
# Relative path to ScionCC sources (in submodule)
SCIONCC_SRC = "extern/scioncc/src"

setup(  name='scion',
        version=VERSION,
        description='SciON',
        long_description=read('README.txt'),
        url='https://github.com/scion-network/scion',
        download_url='https://github.com/scion-network/scion',
        license='BSD',
        author='Michael Meisinger',
        author_email='michael.meisinger@gmail.com',
        keywords=['scion'],
        packages=find_packages('src') + find_packages('.') + (find_packages(SCIONCC_SRC) if INCLUDE_SCIONCC else []),
        package_dir={'': 'src',
                     'interface': 'interface',
                     'defs': 'defs',
                     'ion': SCIONCC_SRC + "/ion",
                     'pyon': SCIONCC_SRC + "/pyon",
                     'putil': SCIONCC_SRC + "/putil",
                     'scripts': SCIONCC_SRC + "/scripts"
        },
        include_package_data=True,
        package_data={
            '': ['*.yml', '*.txt', "*.xml", "*.html"] +
                get_data_dirs("defs", ["*.yml", "*.sql", "*.xml", "*.json", "*.p12", "*.jpg"]) +
                (get_data_dirs(SCIONCC_SRC + "/ion/process/ui", ["*.css", "*.js"]) if INCLUDE_SCIONCC else []),
        },
        dependency_links=[
        ],

        entry_points={
            'console_scripts' : [
                'pycc=scripts.pycc:entry',
                'generate_interfaces=scripts.generate_interfaces:main',
                'store_interfaces=scripts.store_interfaces:main',
                'clear_db=pyon.datastore.clear_couch_util:main',
                ]
            },
        install_requires=[
            # NOTE: Install order is bottom to top! Lower level dependencies need to be down
            'yoyo-migrations==4.2.5',
            'shapely==1.5.7',
            #'pyproj==1.9.4',
            #'tables==3.2.2',
            'h5py==2.5.0',
            'Cython==0.23.4',

            # Pin dependent libraries
            # Last (because dependencies installed first) scioncc with largest number of pinned dependencies
            'scioncc',

        ],
        extras_require={
            # For KML/XML parsing
            'parsing': [
                'lxml==3.4.2',
                'beautifulsoup4',
            ],
        }
     )
