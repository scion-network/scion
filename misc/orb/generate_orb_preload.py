#!/usr/bin/python

import os
import sys
import argparse
import subprocess

import yaml

sys.path.append(os.environ['ANTELOPE'] + "/data/python")


"""
The following antelope commands extract the required metadata.

# Source antelope paths.
. /opt/antelope/5.5/setup.sh

# Extract network metadata.
dbselect -F ' ' n4_tmp.site

OUTPUT:
N4_060A/MGENC/M40
N4_061Z/MGENC/M40
N4_143B/MGENC/M40
N4_146B/MGENC/M40
N4_152A/MGENC/M40

# Extract M40 network sources currently in orb.
orbstat -s ceusnexport.ucsd.edu:usarray | grep /M40 | tr -s ' ' | cut -f 1 -d ' '

FIELDS:
station ondate        offdate lat   lon         elev   station_name
060A    2014035       -1   27.0361  -80.3618    0.0090 Indiantown, FL, USA                                -    -         0.0000    0.0000  1466699882.63683
061Z    2014038       -1   25.8657  -80.9070    0.0090 Ochoppi, FL, USA                                   -    -         0.0000    0.0000  1466699885.20801
143B    2014030       -1   32.7032  -91.4036    0.0310 Socs Landing, Pioneer, LA, USA                     -    -         0.0000    0.0000  1466699891.54217
...
"""

def extract_metadata(db_path, orb_name, network_name):
  """
  Extract metadata from orb and datascope database.
  @param orb_name Name:port of orb.
  @param db_path Path to datascope main file.
  @retval List of metadata structures for each source.
  """

  args = ['dbselect', '-F', ' ', db_path+'.site']
  site_data = subprocess.check_output(args)
  site_data = site_data.split('\n')

  cmd = "orbstat -s ceusnexport.ucsd.edu:usarray | grep /M40 | tr -s ' ' | cut -f 1 -d ' '"
  orb_data = subprocess.check_output(cmd, shell=True)
  orb_data = orb_data.split('\n')
  orb_stations = [x.split('/')[0].split('_')[1] for x in orb_data if x != '']

  metadata = []
  for site in site_data:
    if not site:
      break
    site = site.split()
    station = site[0]
    ondate = site[1]
    offdate = site[2]
    lat = float(site[3])
    lon = float(site[4])
    elev = float(site[5])
    station_name = ' '.join(site[6:-5]).replace("'","")
    select = [i for i,j in enumerate(orb_data) if station in j]
    if not select:
      print 'No orb source has station ' + station
      continue
    select = orb_data[select[0]]
    if offdate != '-1':
      print 'Station %s decomissioned, ignoring.' % station
      continue
    if orb_stations:
      if station not in orb_stations:
        print 'Station %s not found in orb, ignoring.' % station
        continue
    instrument = {'action': 'resource:Instrument',
      'id': 'IN_sensor_ceusn_'+station,
      'owner': 'USER_jdoe',
      'resource': {'agent_info': [{'agent_type': 'data_agent',
                                   'config': {'auto_streaming': True,
                                              'orb_name': orb_name,
                                              'plugin': 'scion.agent.model.orb.orb_plugin.Orb_DataAgentPlugin',
                                              'sampling_interval': 5,
                                              'select': select,
                                              'stream_name': 'basic_streams',
                                              'timeout': 5}}],
                   'description': station_name,
                   'location[GeospatialLocation].latitude': lat,
                   'location[GeospatialLocation].longitude': lon,
                   'model_info': {'model_group': network_name + ' stations'},
                   'name': '%s station %s' %  (network_name, station)}} 
    dataset = {'action': 'resource:Dataset',
      'associations': ['FROM,IN_sensor_ceusn_%s,hasDataset' % station],
      'id': 'DS_sensor_ceusn_'+station,
      'owner': 'USER_jdoe',
      'resource': {'name': 'Dataset Sensor %s %s' % (network_name, station)}, 
      'schema_def': 'ds_orb_mgenc_m40'}
    metadata.append(instrument)
    metadata.append(dataset)
  return metadata

def generate_preload(metadata, network_name):
  """
  Create an orb array datasource preload yml file.
  @param metadata Metadata of orb sources.
  """
  fname = '%s_preload.yml' % network_name
  f = open(fname,'w')
  f.write('# Preload file \n\n')
  f.write('preload_type: steps\n\n')
  f.write('actions:\n\n')
  f.write('# '+ '-'*75 + '\n')
  f.write('# %s data sources\n\n' % network_name)
  yaml.dump(metadata,f)


if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Create an orb source preload file.')
  parser.add_argument('orb_name', help='Name:port of orb source, e.g. ceusnexport.ucsd.edu:usarray.')
  parser.add_argument('db_path', help='Path to the datascope database main file, e.g. orb_sources/n4_dbmaster/n4_tmp.')
  parser.add_argument('network_name', help='Name of the sensor network, e.g. CEUSN.')
  args = parser.parse_args()

  metadata = extract_metadata(args.db_path, args.orb_name, args.network_name)
  generate_preload(metadata, args.network_name)







