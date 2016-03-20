#!/usr/bin/python

import os
import sys
import pickle
import signal
import argparse
import json
import shutil

sys.path.append(os.environ['ANTELOPE'] + "/data/python")

import antelope.orb as orb
import antelope.Pkt as Pkt
import antelope.brttpkt as brttpkt

"""
python orbstart.py --help
python orbstart.py taexport.ucsd.edu:usarrayTA TA_109C/MGENC/M40
"""


def parse_packet(pkt):
  """
  Parse a generic orb packet into a dict with primitive types.
  @param pkt The orb packet.
  @retval A dictionary representation of the packet.
  """
  pkt_data = {}
  pkt_data['db'] = pkt.db
  pkt_data['dfile'] = pkt.dfile
  if pkt.pf:
    pkt_data['pf'] = pkt.pf.pf2dict()
  else:
    pkt_data['pf'] = None
  pkt_data['srcname'] = str(pkt.srcname)
  pkt_data['string'] = pkt.string
  pkt_data['type'] = {}
  pkt_data['type']['content'] = pkt.type.content
  pkt_data['type']['name'] = pkt.type.name
  pkt_data['type']['suffix'] = pkt.type.suffix
  pkt_data['type']['hdrcode'] = pkt.type.hdrcode
  pkt_data['type']['bodycode'] = pkt.type.bodycode
  pkt_data['type']['desc'] = pkt.type.desc
  pkt_data['version'] = pkt.version
  pkt_data['channels'] = []
  for c in pkt.channels:
    channel = {}
    channel['calib'] = c.calib
    channel['calper'] = c.calper
    channel['chan'] = c.chan
    channel['cuser1'] = c.cuser1
    channel['cuser2'] = c.cuser2
    channel['data'] = 'array of int or float data'
    channel['duser1'] = c.duser1
    channel['duser2'] = c.duser2
    channel['iuser1'] = c.iuser1
    channel['iuser2'] = c.iuser2
    channel['iuser3'] = c.iuser3
    channel['loc'] = c.loc
    channel['net'] = c.net
    channel['nsamp'] = c.nsamp
    channel['samprate'] = c.samprate
    channel['segtype'] = c.segtype
    channel['sta'] = c.sta
    channel['time'] = c.time
    pkt_data['channels'].append(channel)
  return pkt_data

done = False

def orb_start(orbname, select=None, reject=None, after=-1, timeout=-1, queuesize=100):
  """
  Start and read an orb reap thread until signaled. 
  """
  # Handle break signal.
  def sig_handler(signum, frame):
    print 'Orb reap got signal ', signum
    global done
    done = True
  signal.signal(signal.SIGTERM, sig_handler)

  print 'entering orb reap...'
  with brttpkt.OrbreapThr(orbname, select=select, reject=reject, after=after, timeout=timeout, queuesize=queuesize) as orbth:
    data_dir = None
    while not done:
      try:
        pktid, srcname, time, packet = orbth.get()
      except brttpkt.Timeout:
        print 'Timeout waiting for orb...'
      except brttpkt.NoData:
        print 'No source data in orb...'
      else:
        orbpkt = Pkt.Packet(srcname, time, packet)
        print pktid, srcname, time, len(packet), str(done)
        pkt_data = parse_packet(orbpkt)
        if not data_dir:
          data_dir = '/tmp/scion-data/%s/' % srcname.replace('/','-')
          if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
          os.makedirs(data_dir)
        fpath = '/tmp/scion-data/%s/pkt_%i.json' % (srcname.replace('/','-'), pktid)
        print 'writing packet %s' % fpath
        f = open(fpath, 'w')
        json.dump(pkt_data, f)
        f.close()

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Start an orb reap process.')
  parser.add_argument('orb_name', help='Name:port of orb source, taexport.ucsd.edu:usarrayTA.')
  parser.add_argument('select', help='Select regex, data source name TA_109C/MGENC/M40.')
  parser.add_argument('--reject', help='Reject regex.', default=None)
  parser.add_argument('--after', help='Begin collection after packet ID..', type=int, default=-1)
  parser.add_argument('--timeout', help='Timeout to read orb, for long interval data.', type=int, default=-1)
  parser.add_argument('--qsize', help='Size of async FIFO queue.', type=int, default=100)
  args = parser.parse_args()

  orb_start(args.orb_name, args.select, args.reject, args.after, args.timeout, args.qsize)

