#!/usr/bin/env python


import subprocess

cmd = ". /opt/antelope/5.5/setup.sh;orbstat -s ceusnexport.ucsd.edu:usarray | grep M40 | grep seconds | cut -d' ' -f1"

max_sources = 5

res = subprocess.check_output(cmd, shell=True)
all_sources = res.split()

#if max_sources:
#  sources = all_sources[0:max_sources]
#else:
#  sources = all_sources

sources = all_sources

print 'retrieved %i of %i M40 sources with seconds latency' % (len(sources), len(all_sources))

