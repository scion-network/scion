#!/usr/bin/env python


import subprocess

from pyon.public import CFG

antelope_path = CFG.get_safe("scion.antelope.path", "/opt/antelope/5.6")
cmd = ". " + antelope_path + "/setup.sh;orbstat -s ceusnexport.ucsd.edu:usarray | grep M40 | grep seconds | cut -d' ' -f1"

max_sources = 5

res = subprocess.check_output(cmd, shell=True)
all_sources = res.split()

#if max_sources:
#  sources = all_sources[0:max_sources]
#else:
#  sources = all_sources

sources = all_sources

print 'retrieved %i of %i M40 sources with seconds latency' % (len(sources), len(all_sources))

